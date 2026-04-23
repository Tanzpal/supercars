import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import MySQLdb.cursors
from datetime import datetime, timedelta

# ------------------------------------------------------------
# 1. FLASK APP SETUP
# ------------------------------------------------------------
app = Flask(__name__)

# Secret key for sessions & secure tokens
app.secret_key = 'supercars_secret_key'


# ------------------------------------------------------------
# 2. MYSQL DATABASE CONFIGURATION
# ------------------------------------------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Test@123'
app.config['MYSQL_DB'] = 'supercars_db'

mysql = MySQL(app)

# Folder to store uploaded images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ------------------------------------------------------------
# 3. EMAIL (Flask-Mail) CONFIGURATION
# ------------------------------------------------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'bikesbay@gmail.com'
app.config['MAIL_PASSWORD'] = 'enwlipwlzwoeirqo'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_DEFAULT_SENDER'] = ('Cars Bay', 'your_email@gmail.com')

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

    # Email to seller
    msg = Message(
        "Your Car Has Been Verified!",
        sender="carsbay@gmail.com",
        recipients=[seller_email]
    )
    msg.body = f"""
Hello {seller_name},

Your car has been VERIFIED by our team!

We will visit your place within 2–5 days for manual verification.

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
@app.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment_page():
    if 'email' not in session:
        flash("Please log in to book an appointment.", "danger")
        return redirect(url_for('show_login'))

    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        phone = request.form['phone']
        vehicle = request.form['vehicle']
        date_str = request.form['date']
        time = request.form['time']
        area = request.form['area']
        city = request.form['city']
        state = request.form['state']
        post_code = request.form['post_code']
        driving_license = request.form['driving_license']
        license_number = request.form.get('license_number')

        # Validate appointment date (min 3 days later)
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        min_date = (datetime.today() + timedelta(days=3)).date()

        if appointment_date < min_date:
            flash(f"You can book appointments from {min_date} onwards.", "danger")
            return redirect(url_for('book_appointment_page'))

        # Insert appointment
        cursor = mysql.connection.cursor()
        query = """
            INSERT INTO appointments 
            (user_email, name, phone, vehicle, date, time, area, city, state, post_code, driving_license, license_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            session['email'], name, phone, vehicle, date_str, time, area, city, state,
            post_code, driving_license, license_number
        ))
        mysql.connection.commit()
        cursor.close()

        # ----------------------------------------------------
        # SEND EMAIL CONFIRMATION FOR APPOINTMENT
        # ----------------------------------------------------
        try:
            subject = "Appointment Confirmation – CarsBay"
            msg = Message(
                subject,
                sender="carsbay@gmail.com",
                recipients=[session['email']]
            )

            msg.body = f"""
Dear {name},

Your appointment has been successfully booked with CarsBay.

Below are your appointment details:

• Vehicle: {vehicle}
• Date: {date_str}
• Time: {time}
• Area: {area}
• City: {city}, {state} – {post_code}
• Driving License: {driving_license}
• License Number: {license_number}

Our team will contact you if any further information is needed before your test ride.

Thank you for choosing CarsBay!

Warm Regards,
CarsBay Team
"""

            mail.send(msg)

        except Exception as email_error:
            print("Email Error:", email_error)
            flash("Appointment booked, but the confirmation email could not be sent.", "warning")

        flash("Appointment booked successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('BookAppointment.html')



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
            # Form data
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            chassis = request.form['chassis']
            plate = request.form['plate']
            years_used = request.form['years_used']
            owners = request.form['owners']
            rc_image = request.files['rc_image']
            car_image = request.files['car_image']

            # Save images
            rc_path = os.path.join(app.config['UPLOAD_FOLDER'], rc_image.filename)
            car_path = os.path.join(app.config['UPLOAD_FOLDER'], car_image.filename)
            rc_image.save(rc_path)
            car_image.save(car_path)

            # Save to DB
            cursor = mysql.connection.cursor()
            sql = """
                INSERT INTO resale_cars 
                (name, email, phone, address, chassis, plate, rc_image, car_image, years_used, owners)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (name, email, phone, address, chassis, plate, rc_path, car_path, years_used, owners))
            mysql.connection.commit()
            cursor.close()

            # ----------------------------------------------------
            # SEND FORMAL EMAIL TO USER (CONFIRMATION)
            # ----------------------------------------------------
            try:
                subject = "Car Submission Received – Under Review | CarsBay"
                msg = Message(
                    subject,
                    sender="carsbay@gmail.com",
                    recipients=[email]
                )

                msg.body = f"""
Dear {name},

Thank you for submitting your car details on CarsBay.

We have successfully received your listing and our verification team will now begin reviewing the following information:

• Chassis Number: {chassis}
• License Plate: {plate}
• Years Used: {years_used}
• Number of Previous Owners: {owners}

Our team will carefully evaluate your submission to ensure it meets our quality and authenticity standards. 
If any additional details or clarification are required, we will contact you directly at {email} or {phone}.

You will receive another email once the review process is complete.

Thank you for choosing CarsBay as your trusted platform for selling your motorcycle.

Warm regards,  
CarsBay Verification Team
"""

                mail.send(msg)

            except Exception as email_error:
                print("Email Error:", email_error)
                flash("Car details submitted, but email could not be sent.", "warning")

            flash("Car details submitted successfully!", "success")
            return redirect(url_for('home'))

        except Exception as e:
            print("Error:", e)
            flash("Something went wrong. Try again.", "danger")
            return redirect(url_for('sell_car_page'))

    return render_template('resale.html')



# ------------------------------------------------------------
# 15. USER DASHBOARD
# ------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('show_login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # User wishlist
    cur.execute("SELECT id, car_name, car_image, car_link FROM wishlist WHERE user_email=%s", (session['email'],))
    wishlist_items = cur.fetchall()

    # User appointments
    cur.execute("SELECT id, vehicle, date, time, area, city FROM appointments WHERE user_email=%s", (session['email'],))
    appointments = cur.fetchall()

    cur.close()

    return render_template(
        'dashboard.html',
        username=session['username'],
        wishlist=wishlist_items,
        appointments=appointments
    )


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
    return render_template('SportsCar.html')

@app.route('/Sedan')
def sedan():
    return render_template('Sedan.html')

@app.route('/XUV')
def XUV():
    return render_template('XUV.html')

# resell form route
@app.route('/ResaleForm')
def ResaleForm():
    return render_template('ResaleForm.html')
# ------------------------------------------------------------
# 21. RUN THE APP
# ------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
