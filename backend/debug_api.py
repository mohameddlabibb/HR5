import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from app import app
app.testing=True
with app.test_client() as c:
    for path in ['/api/sidebar','/api/admin/settings','/api/admin/menus','/api/admin/widgets']:
        r=c.get(path)
        print(path, '->', r.status_code)
        print(r.data[:200])