# ============================================================
# config.example.py — TEMPLATE (safe to commit to git)
# ============================================================
# DO NOT put real credentials here.
# Rename/copy this file to config.py and fill in your values.
# ============================================================

# --- Flask ---
SECRET_KEY = 'change-me-to-a-random-secret-key'

# --- MySQL Database ---
MYSQL_HOST     = 'localhost'
MYSQL_USER     = 'root'
MYSQL_PASSWORD = 'your_mysql_password'
MYSQL_DB       = 'supercars_db'

# --- Email (Flask-Mail) ---
MAIL_SERVER         = 'smtp.gmail.com'
MAIL_PORT           = 587
MAIL_USE_TLS        = True
MAIL_USERNAME       = 'your_email@gmail.com'
MAIL_PASSWORD       = 'your_gmail_app_password'
MAIL_DEFAULT_SENDER = ('Cars Bay', 'your_email@gmail.com')

# --- Blockchain ---
GANACHE_URL = 'http://127.0.0.1:8545'
