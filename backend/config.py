# backend/config.py
# Configuration file for the Flask backend, including admin credentials.
# In a production environment, consider using environment variables for sensitive data.

from werkzeug.security import generate_password_hash

# --- Admin Credentials ---
# Default admin username.
ADMIN_USERNAME = "admin"

# Hashed password for the admin user.
# To change the password:
# 1. Open a Python shell (with your virtual environment activated).
# 2. Run: from werkzeug.security import generate_password_hash; print(generate_password_hash("your_new_secret_password"))
# 3. Copy the output hash string and paste it below.
ADMIN_PASSWORD_HASH = generate_password_hash("adminpass") # Default password is 'adminpass'
