# debug_admin_panel.py
# Small diagnostic script to exercise /admin_panel and print traceback if it crashes.
import os
import sys
import traceback

# Ensure backend directory on path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import app

app.testing = True
app.debug = True

try:
    with app.test_client() as client:
        resp = client.get('/admin_panel')
        print('STATUS_CODE:', resp.status_code)
        print('RESPONSE_SNIPPET:', resp.data.decode(errors='ignore')[:300])
except Exception:
    print('EXCEPTION TRACEBACK:\n')
    traceback.print_exc()