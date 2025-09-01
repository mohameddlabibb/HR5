import os
import sys

# Ensure the backend directory is on the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the Flask app instance from app.py
from app import app

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
