# backend/app.py
# Flask application for the Somabay Handbook backend API.
# Provides API endpoints for managing handbook content, sidebar structure, and admin authentication.

import os
import sys
sys.path.append('.')
import json
import uuid
import secrets
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import bleach

# Define allowed HTML tags and attributes for bleach
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'p', 'strong', 'ul',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'hr', 'div', 'span', 'img', 'video', 'source',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'pre', 'code', 'iframe'
]
ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'style'], # Allow class, id, style on all elements
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'width', 'height'],
    'video': ['src', 'controls', 'width', 'height', 'autoplay', 'loop', 'muted', 'poster'],
    'source': ['src', 'type'],
    'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen']
}

# Import admin credentials from config.py
from backend.config import ADMIN_USERNAME, ADMIN_PASSWORD_HASH
# Import database helper functions
from backend.database import create_connection, add_page_db, get_all_pages_db, get_page_by_id_db, get_page_by_slug_db, update_page_db, delete_page_db

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, static_folder='/public', static_url_path='/public')

def generate_breadcrumbs(slug, flat_pages):
    """Generates breadcrumbs for a given page slug."""
    breadcrumbs = []
    print(f"generate_breadcrumbs called with slug: {slug} and flat_pages: {flat_pages}")
    current_page = next((p for p in flat_pages if p['slug'] == slug), None)

    if not current_page:
        print(f"Current page not found for slug: {slug}")
        return breadcrumbs

    print(f"Current page: {current_page}")
    breadcrumbs.append({'title': 'Home', 'url': '/index.html', 'active': False})

    parent_id = current_page['parent_id']
    while parent_id:
        parent_page = next((p for p in flat_pages if p['id'] == parent_id), None)
        if not parent_page:
            break
        breadcrumbs.insert(1, {'title': parent_page['title'], 'url': f"/pages/{parent_page['slug']}", 'active': False})
        parent_id = parent_page['parent_id']

    breadcrumbs.append({'title': current_page['title'], 'url': None, 'active': True})
    return breadcrumbs

    breadcrumbs.append({'title': 'Home', 'url': '/index.html', 'active': False})

    parent_id = current_page['parent_id']
    while parent_id:
        parent_page = next((p for p in flat_pages if p['id'] == parent_id), None)
        if not parent_page:
            break
        breadcrumbs.insert(1, {'title': parent_page['title'], 'url': f"/pages/{parent_page['slug']}", 'active': False})
        parent_id = parent_page['parent_id']

    breadcrumbs.append({'title': current_page['title'], 'url': None, 'active': True})
    return breadcrumbs
# Enable CORS for all origins. In a production environment, you should restrict this
# to specific origins (e.g., your frontend URL).
CORS(app)
app.config['SECRET_KEY'] = 'somabay_handbook' # Used for session management

DATABASE = 'site.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # This makes rows behave like dictionaries
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Configuration ---
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'uploads')
# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- Helper Functions ---

def find_item_in_sidebar(items, item_id):
    """Recursively finds an item by its ID in the sidebar structure."""
    for item in items:
        if item['id'] == item_id:
            return item
        if 'children' in item and item['children']:
            found_child = find_item_in_sidebar(item['children'], item_id)
            if found_child:
                return found_child
    return None

def find_parent_of_item(items, item_id, parent=None):
    """Recursively finds the parent of an item by its ID in the sidebar structure."""
    for item in items:
        if item['id'] == item_id:
            return parent
        if 'children' in item and item['children']:
            found_parent = find_parent_of_item(item['children'], item_id, item)
            if found_parent:
                return found_parent
    return None

def remove_item_from_sidebar(items, item_id):
    """Recursively removes an item by its ID from the sidebar structure."""
    initial_len = len(items)
    items[:] = [item for item in items if item['id'] != item_id]
    if len(items) < initial_len:
        return True # Item found and removed at this level

    for item in items:
        if 'children' in item and item['children']:
            if remove_item_from_sidebar(item['children'], item_id):
                return True
    return False

def flatten_sidebar(items):
    """Flattens the nested sidebar structure into a single list."""
    flat_list = []
    for item in items:
        flat_list.append(item)
        if 'children' in item and item['children']:
            flat_list.extend(flatten_sidebar(item['children']))
    return flat_list

def update_item_in_sidebar(items, updated_item_data):
    """Recursively updates an item in the sidebar structure."""
    for i, item in enumerate(items):
        if item['id'] == updated_item_data['id']:
            # Update fields, but preserve 'children' if it's a chapter
            if 'children' in item and item['children'] and not updated_item_data.get('is_chapter', False):
                # If it was a chapter and now it's not, clear children
                item.pop('children', None)
            elif updated_item_data.get('is_chapter', False) and 'children' not in item:
                item['children'] = [] # If it's now a chapter, ensure children list exists

            # Update all fields from updated_item_data, except 'id' and 'children' (handled above)
            for key, value in updated_item_data.items():
                if key not in ['id', 'children', 'parent_id', 'is_chapter']: # parent_id and is_chapter are for logic, not direct storage
                    item[key] = value
            return True
        if 'children' in item and item['children']:
            if update_item_in_sidebar(item['children'], updated_item_data):
                return True
    return False

def build_nested_pages(flat_pages, parent_id=None):
    """
    Builds a nested page structure from a flat list of pages.
    Assumes pages have 'id', 'parent_id', and 'is_chapter' fields.
    """
    nested_items = []
    for page in flat_pages:
        if page['parent_id'] == parent_id:
            new_item = page.copy()
            if new_item['is_chapter']:
                new_item['children'] = build_nested_pages(flat_pages, new_item['id'])
            nested_items.append(new_item)
    return nested_items

# --- Database Helper Functions for Settings ---

def get_setting(key):
    """Retrieves a setting value from the database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = ?", (key,))
    result = cursor.fetchone()
    return result[0] if result else None

def update_setting(key, value):
    """Inserts or updates a setting value in the database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES (?, ?)", (key, value))
    db.commit()

# --- Database Helper Functions for Menus ---

def get_all_menus():
    """Retrieves all menus from the database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM menus")
    return [dict(row) for row in cursor.fetchall()]

def get_menu_by_name(name):
    """Retrieves a single menu by its name."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM menus WHERE name = ?", (name,))
    result = cursor.fetchone()
    return dict(result) if result else None

def create_menu(name, menu_data):
    """Creates a new menu."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO menus (name, menu_data) VALUES (?, ?)", (name, json.dumps(menu_data)))
    db.commit()
    return cursor.lastrowid

def update_menu(name, menu_data):
    """Updates an existing menu."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE menus SET menu_data = ? WHERE name = ?", (json.dumps(menu_data), name))
    db.commit()
    return cursor.rowcount

def delete_menu(name):
    """Deletes a menu by its name."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM menus WHERE name = ?", (name,))
    db.commit()
    return cursor.rowcount

# --- Database Helper Functions for Widgets ---

def get_all_widgets():
    """Retrieves all widgets from the database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM widgets")
    return [dict(row) for row in cursor.fetchall()]

def get_widget_by_name(name):
    """Retrieves a single widget by its name."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM widgets WHERE name = ?", (name,))
    result = cursor.fetchone()
    return dict(result) if result else None

def create_widget(name, widget_type, widget_data):
    """Creates a new widget."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO widgets (name, widget_type, widget_data) VALUES (?, ?, ?)", (name, widget_type, json.dumps(widget_data)))
    db.commit()
    return cursor.lastrowid

def update_widget(name, widget_type, widget_data):
    """Updates an existing widget."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE widgets SET widget_type = ?, widget_data = ? WHERE name = ?", (widget_type, json.dumps(widget_data), name))
    db.commit()
    return cur.rowcount

def delete_widget(name):
    """Deletes a widget by its name."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM widgets WHERE name = ?", (name,))
    db.commit()
    return cur.rowcount

# --- Authentication Decorator ---

def token_required(f):
    """Decorator to protect admin API endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': 'Authorization token is missing!'}), 401

        try:
            token_type, token = auth_header.split()
            if token_type.lower() != 'bearer':
                return jsonify({'message': 'Invalid token type!'}), 401

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE token = ?", (token,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'message': 'Invalid token!'}), 401

            # Store the username in the request context for later use if needed
            g.username = user['username']
        except ValueError:
            return jsonify({'message': 'Invalid Authorization header format!'}), 401

        return f(*args, **kwargs)
    return decorated

# --- API Endpoints ---

@app.route('/api/sidebar', methods=['GET'])
def get_sidebar():
    """
    GET /api/sidebar
    Returns the complete sidebar navigation structure from the database.
    This endpoint is public and does not require authentication.
    """
    conn = get_db()
    flat_pages = get_all_pages_db(conn)

    # Build the nested structure from the flat list
    nested_pages = build_nested_pages(flat_pages)

    # Filter out draft pages for public view
    def filter_published(items):
        filtered = []
        for item in items:
            try:
                if item.get('published', False):  # Only include published items
                    new_item = item.copy()
                    if 'children' in new_item:
                        new_item['children'] = filter_published(new_item['children'])
                    filtered.append(new_item)
            except Exception as e:
                print(f"Error filtering item {item.get('id', 'unknown')}: {e}")
        return filtered

    public_sidebar = filter_published(nested_pages)
    print(f"Public Sidebar Data: {public_sidebar}")  # Debugging line
    return jsonify(public_sidebar)


@app.route('/api/pages/<slug>', methods=['GET'])
def get_page(slug):
    """
    GET /api/pages/<slug>
    Returns a single page by its slug.
    """
    conn = get_db()
    page = get_page_by_slug_db(conn, slug)
    if page:
        # Fetch all pages for breadcrumb generation
        flat_pages = get_all_pages_db(conn)
        breadcrumbs = generate_breadcrumbs(slug, flat_pages)
        # Sanitize HTML content using the defined ALLOWED_TAGS and ALLOWED_ATTRIBUTES
        sanitized_content = bleach.clean(page['content'], tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        return jsonify({'title': page['title'], 'content': sanitized_content, 'breadcrumbs': breadcrumbs}), 200
    return jsonify({'message': 'Page not found'}), 404


@app.route('/api/admin/settings', methods=['GET'])
@token_required
def get_cms_settings():
    """
    GET /api/admin/settings
    Retrieves all CMS settings. Requires authentication.
    """
    settings = {
        "site_title": get_setting("site_title"),
        "footer_text": get_setting("footer_text"),
        "social_facebook": get_setting("social_facebook"),
        "social_twitter": get_setting("social_twitter"),
        # Add other settings here as needed
    }
    return jsonify(settings), 200

@app.route('/api/admin/settings', methods=['PUT'])
@token_required
def update_cms_settings():
    """
    PUT /api/admin/settings
    Updates CMS settings. Requires authentication.
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    for key, value in data.items():
        # Only allow specific keys to be updated
        if key in ["site_title", "footer_text", "social_facebook", "social_twitter"]:
            update_setting(key, value)
        else:
            print(f"Attempted to update unauthorized setting key: {key}")

    return jsonify({'message': 'CMS settings updated successfully'}), 200

@app.route('/api/admin/register', methods=['POST'])
def admin_register():
    """
    POST /api/admin/register
    Registers a new admin user.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user:
        return jsonify({'message': 'Username already exists'}), 400

    # Hash the password before storing it
    hashed_password = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()

    return jsonify({'message': 'Registration successful'}), 201

@app.route('/api/admin/menus', methods=['GET'])
@token_required
def get_menus():
    """
    GET /api/admin/menus
    Retrieves all menus. Requires authentication.
    """
    menus = get_all_menus()
    # Parse menu_data from JSON string back to Python object
    for menu in menus:
        if menu['menu_data']:
            menu['menu_data'] = json.loads(menu['menu_data'])
    return jsonify(menus), 200

@app.route('/api/admin/menus', methods=['POST'])
@token_required
def add_menu():
    """
    POST /api/admin/menus
    Adds a new menu. Requires authentication.
    """
    data = request.get_json()
    name = data.get('name')
    menu_data = data.get('menu_data', [])

    if not name:
        return jsonify({'message': 'Menu name is required'}), 400

    if get_menu_by_name(name):
        return jsonify({'message': 'Menu with this name already exists'}), 409

    create_menu(name, menu_data)
    return jsonify({'message': 'Menu created successfully', 'name': name}), 201

@app.route('/api/admin/menus/<name>', methods=['GET'])
@token_required
def get_single_menu(name):
    """
    GET /api/admin/menus/<name>
    Retrieves a single menu by name. Requires authentication.
    """
    menu = get_menu_by_name(name)
    if not menu:
        return jsonify({'message': 'Menu not found'}), 404
    if menu['menu_data']:
        menu['menu_data'] = json.loads(menu['menu_data'])
    return jsonify(menu), 200

@app.route('/api/admin/menus/<name>', methods=['PUT'])
@token_required
def update_single_menu(name):
    """
    PUT /api/admin/menus/<name>
    Updates an existing menu. Requires authentication.
    """
    data = request.get_json()
    menu_data = data.get('menu_data')

    if menu_data is None:
        return jsonify({'message': 'Menu data is required'}), 400

    if update_menu(name, menu_data):
        return jsonify({'message': 'Menu updated successfully', 'name': name}), 200
    return jsonify({'message': 'Menu not found or no changes made'}), 404

@app.route('/api/admin/menus/<name>', methods=['DELETE'])
@token_required
def delete_single_menu(name):
    """
    DELETE /api/admin/menus/<name>
    Deletes a menu by its name. Requires authentication.
    """
    if delete_menu(name):
        return jsonify({'message': 'Menu deleted successfully', 'name': name}), 200
    return jsonify({'message': 'Menu not found'}), 404

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """
    POST /api/admin/login
    Handles admin login. Checks username and hashed password.
    Returns a JSON response with an access token on success.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            app.logger.error("Login attempt with no JSON data")
            return jsonify({'message': 'No login data provided'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            app.logger.error(f"Login attempt with missing credentials. Username: {username}, Password provided: {bool(password)}")
            return jsonify({'message': 'Username and password are required'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['username'] = username
            token = secrets.token_hex(32)
            cursor.execute("UPDATE users SET token = ? WHERE username = ?", (token, username))
            conn.commit()
            conn.close()

            session['adminToken'] = token
            app.logger.info(f"User '{username}' logged in successfully.")
            return jsonify({'message': 'Login successful', 'access_token': token}), 200
        else:
            app.logger.warning(f"Failed login attempt for username: '{username}'. Invalid credentials.")
            conn.close()
            return jsonify({'message': 'Invalid credentials'}), 401

    except Exception as e:
        app.logger.exception(f"An unexpected error occurred during login: {e}")
        # Always return JSON, never HTML
        return jsonify({'message': 'An internal server error occurred', 'error': str(e)}), 500

@app.route('/api/admin/widgets', methods=['GET'])
@token_required
def get_widgets():
    """
    GET /api/admin/widgets
    Retrieves all widgets. Requires authentication.
    """
    widgets = get_all_widgets()
    for widget in widgets:
        if widget['widget_data']:
            widget['widget_data'] = json.loads(widget['widget_data'])
    return jsonify(widgets), 200

@app.route('/api/admin/widgets', methods=['POST'])
@token_required
def add_widget():
    """
    POST /api/admin/widgets
    Adds a new widget. Requires authentication.
    """
    data = request.get_json()
    name = data.get('name')
    widget_type = data.get('widget_type')
    widget_data = data.get('widget_data', {})

    if not name or not widget_type:
        return jsonify({'message': 'Widget name and type are required'}), 400

    if get_widget_by_name(name):
        return jsonify({'message': 'Widget with this name already exists'}), 409

    create_widget(name, widget_type, widget_data)
    return jsonify({'message': 'Widget created successfully', 'name': name}), 201

@app.route('/api/admin/widgets/<name>', methods=['GET'])
@token_required
def get_single_widget(name):
    """
    GET /api/admin/widgets/<name>
    Retrieves a single widget by name. Requires authentication.
    """
    widget = get_widget_by_name(name)
    if not widget:
        return jsonify({'message': 'Widget not found'}), 404
    if widget['widget_data']:
        widget['widget_data'] = json.loads(widget['widget_data'])
    return jsonify(widget), 200

@app.route('/api/admin/widgets/<name>', methods=['PUT'])
@token_required
def update_single_widget(name):
    """
    PUT /api/admin/widgets/<name>
    Updates an existing widget. Requires authentication.
    """
    data = request.get_json()
    widget_type = data.get('widget_type')
    widget_data = data.get('widget_data')

    if widget_type is None or widget_data is None:
        return jsonify({'message': 'Widget type and data are required'}), 400

    if update_widget(name, widget_type, widget_data):
        return jsonify({'message': 'Widget updated successfully', 'name': name}), 200
    return jsonify({'message': 'Widget not found or no changes made'}), 404

@app.route('/api/admin/widgets/<name>', methods=['DELETE'])
@token_required
def delete_single_widget(name):
    """
    DELETE /api/admin/widgets/<name>
    Deletes a widget by its name. Requires authentication.
    """
    if delete_widget(name):
        return jsonify({'message': 'Widget deleted successfully', 'name': name}), 200
    return jsonify({'message': 'Widget not found'}), 404

@app.route('/api/admin/pages', methods=['POST'])
@token_required
def add_page():
    """
    POST /api/admin/pages
    Creates a new page with optional image and video.
    """
    data = request.get_json()

    title = data.get('title')
    slug = data.get('slug')
    content = data.get('content')
    placeholder_image = data.get('placeholder_image')
    embedded_video = data.get('embedded_video')

    if not title or not slug:
        return jsonify({'message': 'Title and slug are required'}), 400

    conn = get_db()
    # Check for duplicate slug
    if get_page_by_slug_db(conn, slug):
        return jsonify({'message': 'Slug already exists. Please choose a unique slug.'}), 409

    page_id = str(uuid.uuid4()) # Generate unique ID

    add_page_db(conn,
                page_id=page_id,
                title=title,
                slug=slug,
                content=content,
                published=True,
                is_chapter=False,
                parent_id=None,
                design={},
                meta_description='',
                meta_keywords='',
                custom_css='',
                placeholder_image=placeholder_image,
                embedded_video=embedded_video
    )

    return jsonify({'message': 'Page created successfully', 'page_id': page_id}), 201

@app.route('/api/admin/pages/<slug>', methods=['PUT'])
@token_required
def edit_page(slug):
    """
    PUT /api/admin/pages/<slug>
    Edits an existing page by its slug. Requires authentication.
    """
    data = request.get_json()
    conn = get_db()
    page_to_edit = get_page_by_slug_db(conn, slug)

    if not page_to_edit:
        return jsonify({'message': 'Page not found'}), 404

    # Update fields
    title = data.get('title', page_to_edit['title'])
    new_slug = data.get('slug', page_to_edit['slug'])
    content = data.get('content', page_to_edit['content'])
    published = data.get('published', page_to_edit['published'])
    is_chapter = data.get('is_chapter', page_to_edit['is_chapter'])
    parent_id = data.get('parent_id', page_to_edit['parent_id'])
    design = data.get('design', page_to_edit['design'])
    meta_description = data.get('meta_description', page_to_edit['meta_description'])
    meta_keywords = data.get('meta_keywords', page_to_edit['meta_keywords'])
    custom_css = data.get('custom_css', page_to_edit['custom_css'])
    placeholder_image = data.get('placeholder_image', page_to_edit['placeholder_image'])
    embedded_video = data.get('embedded_video', page_to_edit['embedded_video'])

    # Allow slug change, but check for duplicates if changed
    if new_slug != page_to_edit['slug']:
        if get_page_by_slug_db(conn, new_slug):
            return jsonify({'message': 'New slug already exists. Please choose a unique slug.'}), 409

    update_page_db(conn, page_to_edit['id'], title, new_slug, content, published, is_chapter, parent_id, design, meta_description, meta_keywords, custom_css, placeholder_image, embedded_video)
    
    return jsonify({'message': 'Page updated successfully'}), 200

@app.route('/api/admin/pages/<slug>', methods=['DELETE'])
@token_required
def delete_page(slug):
    """
    DELETE /api/admin/pages/<slug>
    Deletes a page by its slug. Requires authentication.
    """
    conn = get_db()
    page_to_delete = get_page_by_slug_db(conn, slug)

    if not page_to_delete:
        return jsonify({'message': 'Page not found'}), 404

    delete_page_db(conn, page_to_delete['id'])
    return jsonify({'message': 'Page deleted successfully'}), 200

@app.route('/api/admin/pages/<page_id>/visibility', methods=['PUT'])
@token_required
def toggle_page_visibility(page_id):
    """
    PUT /api/admin/pages/<page_id>/visibility
    Toggles the published status of a page. Requires authentication.
    """
    data = request.get_json()
    published_status = data.get('published')

    if published_status is None or not isinstance(published_status, bool):
        return jsonify({'message': 'Invalid published status provided'}), 400

    conn = get_db()
    page_to_update = get_page_by_id_db(conn, page_id)

    if not page_to_update:
        return jsonify({'message': 'Page not found'}), 404

    # Update only the published status
    update_page_db(conn, page_to_update['id'], page_to_update['title'], page_to_update['slug'],
                   page_to_update['content'], published_status, page_to_update['is_chapter'],
                   page_to_update['parent_id'], page_to_update['design'],
                   page_to_update['meta_description'], page_to_update['meta_keywords'],
                   page_to_update['custom_css'], page_to_update['placeholder_image'], page_to_update['embedded_video'])
    
    return jsonify({'message': 'Page visibility updated successfully', 'published': published_status}), 200

@app.route('/api/admin/sidebar/reorder', methods=['PUT'])
@token_required
def reorder_sidebar():
    """
    PUT /api/admin/sidebar/reorder
    Reorders the sidebar structure based on the provided new order. Requires authentication.
    """
    data = request.get_json()
    new_order_list = data.get('sidebar_order')

    if not new_order_list or not isinstance(new_order_list, list):
        return jsonify({'message': 'Invalid sidebar order provided'}), 400

    conn = get_db()

    # Helper to recursively update parent_id
    def update_parent_ids_recursive(items, parent_id=None):
        for item in items:
            page_id = item['id']
            # Fetch existing page data to preserve all fields
            existing_page = get_page_by_id_db(conn, page_id)
            if existing_page:
                update_page_db(conn, page_id, existing_page['title'], existing_page['slug'],
                               existing_page['content'], existing_page['published'], existing_page['is_chapter'],
                               parent_id, existing_page['design'], existing_page['meta_description'],
                               existing_page['meta_keywords'], existing_page['custom_css'],
                               existing_page['image'], existing_page['video'])
            if 'children' in item and item['children']:
                update_parent_ids_recursive(item['children'], page_id)

    update_parent_ids_recursive(new_order_list)

    return jsonify({'message': 'Sidebar order updated successfully'}), 200

@app.route('/api/admin/pages/<page_id>/design', methods=['PUT'])
@token_required
def update_page_design(page_id):
    """
    PUT /api/admin/pages/<page_id>/design
    Updates the design options (header color, image) for a page. Requires authentication.
    """
    data = request.get_json()
    header_color = data.get('headerColor')
    header_image = data.get('headerImage')

    conn = get_db()
    page_to_update = get_page_by_id_db(conn, page_id)

    if not page_to_update:
        return jsonify({'message': 'Page not found'}), 404

    design = page_to_update.get('design', {})

    if header_color is not None:
        design['headerColor'] = header_color
    if header_image is not None:
        design['headerImage'] = header_image

    update_page_db(conn, page_to_update['id'], page_to_update['title'], page_to_update['slug'],
                   page_to_update['content'], page_to_update['published'], page_to_update['is_chapter'],
                   page_to_update['parent_id'], design, page_to_update['meta_description'],
                   page_to_update['meta_keywords'], page_to_update['custom_css'],
                   page_to_update['placeholder_image'], page_to_update['embedded_video'])
    
    return jsonify({'message': 'Page design updated successfully', 'design': design}), 200

@app.route('/api/admin/upload', methods=['POST'])
@token_required
def upload_image():
    """
    POST /api/admin/upload
    Handles image uploads to the public/uploads directory. Requires authentication.
    """
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file:
        # Secure filename and save
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        filepath = os.path.join(UPLOADS_DIR, filename)
        file.save(filepath)
        # Return the public URL for the uploaded file
        return jsonify({'message': 'File uploaded successfully', 'file_path': f'/uploads/{filename}'}), 200
    return jsonify({'message': 'File upload failed'}), 500

@app.route('/admin')
def serve_admin():
    """
    Serves the admin.html file from the public directory.
    """
    return send_from_directory('../public', 'admin.html')


# Upload folder
UPLOAD_FOLDER = os.path.join("public", "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/admin_panel", methods=["GET", "POST"])
def admin_panel():
    if request.method == "POST":
        # Handle uploaded image
        image_file = request.files.get("placeholder_image")
        saved_image_url = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(image_path)
            saved_image_url = f"/static/uploads/{filename}"

        # Handle uploaded video
        video_file = request.files.get("embedded_video")
        saved_video_url = None
        if video_file and allowed_file(video_file.filename):
            filename = secure_filename(video_file.filename)
            video_path = os.path.join(UPLOAD_FOLDER, filename)
            video_file.save(video_path)
            saved_video_url = f"/static/uploads/{filename}"

        # TODO: Save saved_image_url and saved_video_url to DB instead of just printing
        print("Image uploaded at:", saved_image_url)
        print("Video uploaded at:", saved_video_url)

        return redirect(url_for("admin_panel"))

    # For GET request → render your HTML
    return send_from_directory("/public", "admin_panel.html")

@app.route('/')
def serve_index():
    """
    Serves the main index.html file from the public/pages directory.
    """
    return send_from_directory(os.path.join(app.static_folder, 'pages'), 'index.html')

@app.route('/pages/<path:filename>')
def serve_static_page(filename):
    """
    Serves static HTML pages from the public/pages directory.
    """
    return send_from_directory(os.path.join(app.static_folder, 'pages'), filename)

# Example 301 Redirect (uncomment and modify as needed)
# @app.route('/old-placeholder-url')
# def old_url_redirect():
#     return redirect('/pages/new-page-slug.html', code=301)

@app.errorhandler(404)
def page_not_found(e):
    """
    Custom 404 error handler.
    """
    return send_from_directory(os.path.join(app.static_folder, 'pages'), '404.html'), 404

# --- Run the Flask app ---
if __name__ == '__main__':
    # This is for development only. In production, use a WSGI server like Gunicorn.
    app.run(debug=True, port=5000)
