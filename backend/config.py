# backend/config.py
# Configuration file for the Flask backend, including admin credentials.
# For production, consider using environment variables for sensitive data.

# --- Admin Credentials ---
# Default admin username
ADMIN_USERNAME = "admin"

# Hashed password for the admin user.
# Default password is 'adminpass'
# To generate a custom hash:
#   1. Open a Python shell with your virtual environment activated
#   2. Run:
#        from werkzeug.security import generate_password_hash
#        print(generate_password_hash("your_new_password"))
#   3. Copy the output and replace the string below
ADMIN_PASSWORD_HASH = "pbkdf2:sha256:600000$Gs8yZlskc2CfnBPY$892013fd6d3b72de2f9344f8593d6922c691f2591babfc747d96c260f3be11a7"

# --- Server / App Settings (Optional) ---
# You can add other configuration settings here if needed
# e.g., DEBUG mode, secret key, session lifetime, etc.
SECRET_KEY = "b1d8f7c6-2a8d-4bde-b92e-9a7f2f6c1a5e"
DEBUG = True
