import os
import config
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import MySQLdb.cursors
from datetime import datetime, timedelta
from flask import session, redirect, url_for, flash

# Import blockchain modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from blockchain.ownership_contract import buy_shares, get_ownership_status
from blockchain.vehicle_passport import register_car_on_blockchain

# ------------------------------------------------------------
# 1. FLASK APP SETUP
# ------------------------------------------------------------
app = Flask(__name__)

# Secret key for sessions & secure tokens — loaded from config.py (gitignored)
app.secret_key = config.SECRET_KEY


# ------------------------------------------------------------
# 2. MYSQL DATABASE CONFIGURATION
# ------------------------------------------------------------
app.config['MYSQL_HOST']     = config.MYSQL_HOST
app.config['MYSQL_USER']     = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB']       = config.MYSQL_DB

mysql = MySQL(app)

# Folder to store uploaded images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ------------------------------------------------------------
# 3. EMAIL (Flask-Mail) CONFIGURATION
# ------------------------------------------------------------
app.config['MAIL_SERVER']         = config.MAIL_SERVER
app.config['MAIL_PORT']           = config.MAIL_PORT
app.config['MAIL_USERNAME']       = config.MAIL_USERNAME
app.config['MAIL_PASSWORD']       = config.MAIL_PASSWORD
app.config['MAIL_USE_TLS']        = config.MAIL_USE_TLS
app.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER

mail = Mail(app)



# Token generator for password reset emails
s = URLSafeTimedSerializer(app.secret_key)


# ------------------------------------------------------------
# 4. FORGOT PASSWORD — SEND RESET LINK
# ------------------------------------------------------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Check if email exists
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            # Create secure token
            token = s.dumps(email, salt='password-reset-salt')

            # Password reset link
            reset_link = url_for('reset_password', token=token, _external=True)

            # Prepare email
            subject = "🔐 Reset Your Password"
            msg = Message(subject, sender="your_email@gmail.com", recipients=[email])
            msg.body = f"""
You requested a password reset.

Click below to reset your password:
{reset_link}

If this wasn't you, ignore this email.
- Cars Bay Team
"""
            mail.send(msg)
            flash("Password reset link sent to your email!", "success")
        else:
            flash("Email not found!", "danger")

        return redirect(url_for('show_login'))

    return render_template('forgot_password.html')


# ------------------------------------------------------------
# 5. RESET PASSWORD — VALIDATE TOKEN + UPDATE PASSWORD
# ------------------------------------------------------------
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Validate token (valid for 1 hour)
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        return "The reset link has expired."
    except BadSignature:
        return "Invalid reset link."

    if request.method == 'POST':
        new_password = request.form['password']

        # Update password
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password=%s WHERE email=%s", (new_password, email))
        mysql.connection.commit()
        cur.close()

        flash("Password updated successfully!", "success")
        return redirect(url_for('show_login'))

    return render_template('reset_password.html', token=token)


# ------------------------------------------------------------
# 6. LOGIN PAGE
# ------------------------------------------------------------
@app.route('/login', methods=['GET'])
def show_login():
    return render_template('login.html')


# ------------------------------------------------------------
# 7. LOGIN (AUTHENTICATION)
# ------------------------------------------------------------
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()

    if not user:
        flash("Email not found!", "danger")
        return redirect(url_for('show_login'))

    if user['password'] != password:
        flash("Incorrect password!", "danger")
        return redirect(url_for('show_login'))

    # login success
    session['user_id'] = user['id']
    session['username'] = user['name']
    session['email'] = user['email']
    session['is_admin'] = user['is_admin']

    if user['is_admin'] == 1:
        return redirect(url_for('admin_dashboard'))

    return redirect(url_for('dashboard'))



# ------------------------------------------------------------
# 8. ADMIN DASHBOARD
# ------------------------------------------------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('is_admin') != 1:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('dashboard'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch admin data
    cursor.execute("SELECT * FROM appointments ORDER BY id DESC")
    appointments = cursor.fetchall()

    cursor.execute("SELECT * FROM contact_messages ORDER BY id DESC")
    messages = cursor.fetchall()

    cursor.execute("SELECT * FROM resale_cars ORDER BY id DESC")
    cars = cursor.fetchall()

    cursor.close()

    return render_template(
        'admin_dashboard.html',
        appointments=appointments,
        messages=messages,
        cars=cars
    )


# ------------------------------------------------------------
# 9. ADMIN — VERIFY CAR + SEND EMAIL
# ------------------------------------------------------------
@app.route('/verify_car/<int:car_id>')
def verify_car(car_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get seller details
    cursor.execute("SELECT name, email FROM resale_cars WHERE id = %s", (car_id,))
    car = cursor.fetchone()

    if not car:
        flash("Car not found!", "danger")
        return redirect(url_for('admin_dashboard'))

    seller_email = car['email']
    seller_name = car['name']

    # Mark car as verified
    cursor.execute("UPDATE resale_cars SET is_verified = 1 WHERE id = %s", (car_id,))
    mysql.connection.commit()

    # --- Register car on blockchain ---
    bc_result = register_car_on_blockchain(car_id)
    if bc_result['status'] == 'success':
        blockchain_id = bc_result['blockchain_id']
        cursor.execute(
            "UPDATE resale_cars SET blockchain_id = %s WHERE id = %s",
            (blockchain_id, car_id)
        )
        mysql.connection.commit()
        flash(f"Car registered on blockchain. TX: {blockchain_id[:20]}...", "info")
    else:
        flash("Blockchain registration failed: " + bc_result['message'], "warning")

    cursor.close()

    # Email to seller
    msg = Message(
        "Your Car Has Been Verified!",
        sender="carsbay@gmail.com",
        recipients=[seller_email]
    )
    msg.body = f"""
Hello {seller_name},

Your car has been VERIFIED by our team and registered on the blockchain!

Blockchain Record: {bc_result.get('blockchain_id', 'N/A')}

This means your car listing is now tamper-proof and eligible for
fractional ownership by buyers on Cars-Bay.

We will visit your place within 2-5 days for manual verification.

Thank you!
Cars-Bay Team
"""

    try:
        mail.send(msg)
        flash("Car verified and email sent!", "success")
    except Exception as e:
        flash("Car verified, but failed to send email: " + str(e), "warning")

    return redirect(url_for('admin_dashboard'))


# ------------------------------------------------------------
# 10. SIGNUP ROUTE
# ------------------------------------------------------------
@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()

    # Check if user already exists
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    existing_user = cur.fetchone()

    if existing_user:
        cur.close()
        return redirect(url_for('show_login', email_exists='true'))

    # New user
    cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
    mysql.connection.commit()
    cur.close()

    # Send welcome email
    msg = Message(
        "Welcome to Cars Bay!",
        sender=("Cars Bay", "your_email@gmail.com"),
        recipients=[email],
        body=f"Hello {name},\n\nWelcome to Cars Bay! Your account has been created.\n\n- Team Cars Bay"
    )
    mail.send(msg)

    flash("Account created! Please login.", "success")
    return redirect(url_for('show_login'))


# ------------------------------------------------------------
# 11. LOGOUT
# ------------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('show_login'))


# ------------------------------------------------------------
# 12. CONTACT FORM
# ------------------------------------------------------------
@app.route('/contactUs', methods=['GET', 'POST'])
def contactUs():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['mail']
        mob = request.form['mob']
        query = request.form['query']

        # Save in database
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO contact_messages (name, email, phone, query) VALUES (%s, %s, %s, %s)",
            (name, email, mob, query)
        )
        mysql.connection.commit()
        cur.close()

        # -----------------------------
        # SEND EMAIL TO USER
        # -----------------------------
        try:
            subject = "We Received Your Query - CarsBay"
            msg = Message(
                subject,
                sender="carsbay@gmail.com",
                recipients=[email]
            )
            msg.body = f"""
Hello {name},

Thank you for contacting CarsBay!

We have received your query:

"{query}"

Our team will review it and get back to you shortly.

Best Regards,  
CarsBay Support Team
"""

            mail.send(msg)
            flash("Message sent successfully! A confirmation email has been sent.", "success")

        except Exception as e:
            flash("Message saved, but failed to send email: " + str(e), "warning")

        return redirect(url_for('home'))

    return render_template('contactUs.html')



# ------------------------------------------------------------
# 13. BOOK APPOINTMENT
# ------------------------------------------------------------
# app.py (Flask route)
@app.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment_page():
    if 'email' not in session:
        flash("Please log in to book an appointment.", "danger")
        return redirect(url_for('show_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch cars (id + name)
    cursor.execute("SELECT DISTINCT id, car_name FROM resale_cars ORDER BY id DESC")
    cars = cursor.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']

        # ✅ FIX: now using car_id instead of vehicle name
        car_id = request.form['vehicle']

        date_str = request.form['date']
        time = request.form['time']
        area = request.form['area']
        city = request.form['city']
        state = request.form['state']
        post_code = request.form['post_code']
        driving_license = request.form['driving_license']
        license_number = request.form.get('license_number')

        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        min_date = (datetime.today() + timedelta(days=3)).date()

        if appointment_date < min_date:
            flash(f"You can book appointments from {min_date} onwards.", "danger")
            return redirect(url_for('book_appointment_page'))

        # Insert into DB (FIXED COLUMN: car_id)
        cursor.execute("""
            INSERT INTO appointments 
            (user_email, name, phone, car_id, date, time, area, city, state, post_code, driving_license, license_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session['email'], name, phone, car_id, date_str, time,
            area, city, state, post_code, driving_license, license_number
        ))

        mysql.connection.commit()

        # Email
        try:
            msg = Message(
                "Appointment Confirmation – CarsBay",
                sender="carsbay@gmail.com",
                recipients=[session['email']]
            )

            msg.body = f"""
Dear {name},

Your appointment has been successfully booked.

Vehicle ID: {car_id}
Date: {date_str}
Time: {time}
Location: {area}, {city}, {state} - {post_code}

Thank you for choosing CarsBay!
"""
            mail.send(msg)

        except Exception as email_error:
            print("Email Error:", email_error)
            flash("Booked, but email failed.", "warning")

        cursor.close()
        flash("Appointment booked successfully!", "success")
        return redirect(url_for('dashboard'))

    cursor.close()
    return render_template('BookAppointment.html', cars=cars)



# ------------------------------------------------------------
# 13. booked time slots
# ------------------------------------------------------------

@app.route('/get-booked-times')
def get_booked_times():
    selected_date = request.args.get('date')

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = %s", (selected_date,))
    rows = cursor.fetchall()
    cursor.close()

    booked_times = [row[0] for row in rows]

    return jsonify({"booked_times": booked_times})

# ------------------------------------------------------------
# 14. SELL CAR (UPLOAD IMAGES + STORE DETAILS + SEND EMAIL)
# ------------------------------------------------------------
@app.route('/sell-car', methods=['GET', 'POST'])
def sell_car_page():
    if request.method == 'POST':
        try:
            if 'email' not in session:
                flash("Please login first!", "danger")
                return redirect(url_for('show_login'))

            # Get form data
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            email = session['email']   # ✅ FIXED HERE
            phone = request.form['phone']
            car_name = request.form['carName']
            car_type = request.form['carType']
            brand = request.form['brand']
            cc = request.form['cc']
            hp = request.form['hp']
            speed = request.form['speed']
            year = request.form['year']
            owners = request.form['owners']
            price = request.form['price']
            description = request.form['description']

            image = request.files['image']

            # Save image
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_path)

            # Insert into DB
            cursor = mysql.connection.cursor()
            query = """
                INSERT INTO resale_cars 
                (firstname, lastname, email, phone, car_name, car_type, brand, cc, hp, speed, year, owners, price, description, image)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                firstname, lastname, email, phone, car_name, car_type,
                brand, cc, hp, speed, year, owners, price, description, image_path
            ))
            mysql.connection.commit()
            cursor.close()

            flash("Car posted successfully!", "success")
            return redirect(url_for('sportscar'))

        except Exception as e:
            print("Error:", e)
            flash("Error submitting form", "danger")

    return render_template('ResaleForm.html')



# ------------------------------------------------------------
# 15. USER DASHBOARD
# ------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('show_login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Wishlist
    cur.execute(
        "SELECT id, car_name, car_image, car_link FROM wishlist WHERE user_email=%s",
        (session['email'],)
    )
    wishlist_items = cur.fetchall()

    # Appointments
    cur.execute("""
    SELECT a.*, r.car_name
    FROM appointments a
    JOIN resale_cars r ON a.car_id = r.id
""")
    appointments = cur.fetchall()

    # User's fractional ownership stakes
    cur.execute("""
        SELECT o.id, o.shares, o.created_at,
               r.car_name, r.image, r.blockchain_id,
               (SELECT IFNULL(SUM(shares),0) FROM ownership WHERE vehicle_id = o.vehicle_id) as total_shares_sold
        FROM ownership o
        JOIN resale_cars r ON o.vehicle_id = r.id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    """, (session['user_id'],))
    stakes = cur.fetchall()

    # User's posted cars
    cur.execute(
        "SELECT * FROM resale_cars WHERE email=%s ORDER BY id DESC",
        (session['email'],)
    )
    user_cars = cur.fetchall()

    cur.close()

    return render_template(
        'dashboard.html',
        username=session['username'],
        wishlist=wishlist_items,
        appointments=appointments,
        stakes=stakes,
        user_cars=user_cars
    )


# ------------------------------------------------------------
# 16. DELETE BLOCK
# ------------------------------------------------------------

@app.route('/delete_car/<int:car_id>', methods=['POST'])
def delete_car(car_id):
    if 'email' not in session:
        return jsonify({"status": "error", "message": "Login required"}), 401

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check ownership
    cursor.execute("SELECT * FROM resale_cars WHERE id=%s", (car_id,))
    car = cursor.fetchone()

    if not car:
        return jsonify({"status": "error", "message": "Car not found"}), 404

    if car['email'] != session['email']:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    # Delete
    cursor.execute("DELETE FROM resale_cars WHERE id=%s", (car_id,))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"status": "success"})


# ------------------------------------------------------------
# 16. CANCEL APPOINTMENT
# ------------------------------------------------------------
@app.route('/cancel_appointment/<int:appt_id>', methods=['POST'])
def cancel_appointment(appt_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = %s", (appt_id,))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'success': True}), 200


# ------------------------------------------------------------
# 17. WISHLIST — ADD ITEM
# ------------------------------------------------------------
@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    if 'email' not in session:
        return jsonify({'status': 'error', 'message': 'Please login first'})

    data = request.get_json()
    car_name = data.get('car_name')
    car_image = data.get('car_image')
    car_link = data.get('car_link')

    cur = mysql.connection.cursor()

    # Check if already added
    cur.execute("SELECT * FROM wishlist WHERE user_email=%s AND car_name=%s", (session['email'], car_name))
    exists = cur.fetchone()

    if exists:
        cur.close()
        return jsonify({'status': 'exists', 'message': 'Already in wishlist'})

    # Add to wishlist
    cur.execute("INSERT INTO wishlist (user_email, car_name, car_image, car_link) VALUES (%s, %s, %s, %s)",
                (session['email'], car_name, car_image, car_link))
    mysql.connection.commit()
    cur.close()

    return jsonify({'status': 'success', 'message': 'Added to wishlist'})


# ------------------------------------------------------------
# 18. WISHLIST — REMOVE ITEM - direct from UI
# ------------------------------------------------------------

@app.route('/remove_from_wishlist_by_name', methods=['POST'])
def remove_from_wishlist_by_name():
    if 'email' not in session:
        return jsonify({"status": "error", "message": "Please login first"})

    data = request.get_json()
    car_name = data.get("car_name")

    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM wishlist WHERE car_name=%s AND user_email=%s",
        (car_name, session['email'])
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({"status": "success"})


# ------------------------------------------------------------
# 18. WISHLIST — REMOVE ITEM
# ------------------------------------------------------------
@app.route('/remove_from_wishlist', methods=['POST'])
def remove_from_wishlist():
    if 'email' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    data = request.get_json()
    car_id = data.get("car_id")

    if not car_id:
        return jsonify({"status": "error", "message": "No car ID provided"}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM wishlist WHERE id=%s AND user_email=%s", (car_id, session['email']))
        mysql.connection.commit()
        cur.close()

        return jsonify({"status": "success", "message": "Car removed successfully"})
    except Exception as e:
        print("Error removing car:", e)
        return jsonify({"status": "error", "message": "Database error"}), 500


# ------------------------------------------------------------
# 19. STATIC PAGES
# ------------------------------------------------------------
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/sportscar')
def sportscar():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM resale_cars ORDER BY id DESC")
    cars = cursor.fetchall()
    cursor.close()

    return render_template('SportsCar.html', cars=cars)

# ------------------------------------------------------------
# 11. Resalform - Allowance
# ------------------------------------------------------------

@app.route('/ResaleForm')
def ResaleForm():
    if 'username' not in session:
        flash("Please login first to sell your car.")
        return redirect(url_for('show_login'))
    
    return render_template('ResaleForm.html')


# ------------------------------------------------------------
# 20. FRACTIONAL OWNERSHIP API
# ------------------------------------------------------------
@app.route('/api/ownership/status/<int:car_id>', methods=['GET'])
def api_ownership_status(car_id):
    # Get total shares sold from DB first
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT IFNULL(SUM(shares), 0) as total_shares FROM ownership WHERE vehicle_id=%s", (car_id,))
    db_result = cur.fetchone()
    total_db_shares = int(db_result['total_shares']) if db_result and db_result['total_shares'] else 0
    cur.close()

    # Try checking blockchain status
    bc_result = get_ownership_status(car_id)
    
    return jsonify({
        "status": "success", 
        "car_id": car_id, 
        "total_shares_sold": total_db_shares,
        "blockchain_data": bc_result
    })

@app.route('/api/ownership/buy', methods=['POST'])
def api_ownership_buy():
    if 'email' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    data = request.get_json()
    car_id = data.get("car_id")
    shares_amount = data.get("shares")

    if not car_id or not shares_amount:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        shares_amount = int(shares_amount)
        if shares_amount <= 0:
            return jsonify({"status": "error", "message": "Invalid share amount"}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid share amount"}), 400

    # Execute blockchain transaction
    bc_res = buy_shares(car_id, session['email'], shares_amount)

    if bc_res['status'] == 'error':
        return jsonify(bc_res), 500

    # Update DB
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO ownership (vehicle_id, user_id, shares) VALUES (%s, %s, %s)",
            (car_id, session['user_id'], shares_amount)
        )
        mysql.connection.commit()
        cur.close()

        return jsonify({
            "status": "success",
            "message": f"Successfully purchased {shares_amount} shares!",
            "blockchain_tx": bc_res.get("tx_hash", "")
        })
    except Exception as e:
        print("DB Error:", e)
        return jsonify({"status": "error", "message": "Database update failed"}), 500


# ------------------------------------------------------------
# 21. RUN THE APP
# ------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
