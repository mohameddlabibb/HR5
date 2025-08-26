# backend/app.py
# Flask application for the Somabay Handbook backend API.
# Provides API endpoints for managing handbook content, sidebar structure, and admin authentication.

import os
from pydoc import pager
import sys
sys.path.append('.')
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3

# Import admin credentials from config.py
from config import ADMIN_USERNAME, ADMIN_PASSWORD_HASH

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
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
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PAGES_FILE = os.path.join(DATA_DIR, 'pages.json')
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'uploads')
# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- Helper Functions ---

def read_pages_data():
    """Reads the pages data from the JSON file."""
    if not os.path.exists(PAGES_FILE):
        return []
    with open(PAGES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_pages_data(data):
    """Writes the pages data to the JSON file."""
    with open(PAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

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

def reorder_sidebar_structure(current_sidebar, new_order_list):
    """
    Reorders the sidebar structure based on a new order list.
    This function is complex as it needs to handle nested structures.
    """
    # Create a dictionary for quick lookup of items by ID
    item_map = {item['id']: item for item in flatten_sidebar(current_sidebar)}

    def build_nested_order(order_list):
        new_nested_items = []
        for ordered_item in order_list:
            item_id = ordered_item['id']
            original_item = item_map.get(item_id)
            if original_item:
                # Create a copy to avoid modifying the original item_map reference directly
                new_item = original_item.copy()
                if 'children' in ordered_item:
                    new_item['children'] = build_nested_order(ordered_item['children'])
                elif 'children' in new_item: # If original had children but new order doesn't specify, keep them
                    pass # Keep existing children if not explicitly reordered
                new_nested_items.append(new_item)
        return new_nested_items

    return build_nested_order(new_order_list)

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
    return cursor.rowcount

def delete_widget(name):
    """Deletes a widget by its name."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM widgets WHERE name = ?", (name,))
    db.commit()
    return cursor.rowcount

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
            if token_type.lower() != 'bearer' or token != 'admin-token-placeholder': # Simple token check
                return jsonify({'message': 'Invalid token!'}), 401
        except ValueError:
            return jsonify({'message': 'Invalid Authorization header format!'}), 401

        # In a real application, you would decode and validate a JWT here.
        # For this project, we're using a simple placeholder token.
        return f(*args, **kwargs)
    return decorated

# --- API Endpoints ---

@app.route('/api/sidebar', methods=['GET'])
def get_sidebar():
    
    """
    GET /api/sidebar
    Returns the complete sidebar navigation structure from pages.json.
    This endpoint is public and does not require authentication.
    """
    pages = read_pages_data()
    # Filter out draft pages for public view
    def filter_published(items):
        filtered = []
        for item in items:
            try:
                if item.get('published', False): # Only include published items
                    new_item = item.copy()
                    if 'children' in new_item:
                        new_item['children'] = filter_published(new_item['children'])
                    filtered.append(new_item)
            except Exception as e:
                print(f"Error filtering item {item.get('id', 'unknown')}: {e}")
                # Optionally, you could log this error more formally or skip the item
        return filtered
    
    public_sidebar = filter_published(pages)
    print(f"Public Sidebar Data: {public_sidebar}") # Debugging line
    return jsonify(public_sidebar)

@app.route('/api/pages/<slug>', methods=['GET'])
def get_page_content(slug):
    """
    GET /api/pages/<slug>
    Returns the content of a specific page by its slug.
    This endpoint is public and does not require authentication.
    """
    pages = read_pages_data()
    # Flatten the structure to find the page by slug
    all_pages = flatten_sidebar(pages)
    page = next((p for p in all_pages if p.get('slug') == slug and p.get('published', False)), None)

    if page:
        return jsonify(page)
    return jsonify({'message': 'Page not found or not published'}), 404

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
    Deletes a menu by name. Requires authentication.
    """
    if delete_menu(name):
        return jsonify({'message': 'Menu deleted successfully', 'name': name}), 200
    return jsonify({'message': 'Menu not found'}), 404

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """
    POST /api/admin/login
    Handles admin login. Checks username and hashed password.
    Returns a simple access token on success.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user[2], password):
        session['username'] = username
        return jsonify({'message': 'Login successful', 'access_token': 'admin-token-placeholder'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

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
    Deletes a widget by name. Requires authentication.
    """
    if delete_widget(name):
        return jsonify({'message': 'Widget deleted successfully', 'name': name}), 200
    return jsonify({'message': 'Widget not found'}), 404

@app.route('/api/admin/pages', methods=['POST'])
@token_required
def add_page():
    """
    POST /api/admin/pages
    Adds a new page or chapter to the handbook. Requires authentication.
    """
    data = request.get_json()
    title = data.get('title')
    slug = data.get('slug')
    content = data.get('content', '')
    published = data.get('published', False)
    is_chapter = data.get('is_chapter', False)
    parent_id = data.get('parent_id')
    design = data.get('design', {})
    meta_description = data.get('meta_description', '')
    meta_keywords = data.get('meta_keywords', '')
    custom_css = data.get('custom_css', '')

    if not title or (not is_chapter and not slug): # Slug is not required for chapters
        return jsonify({'message': 'Title and slug (for pages) are required'}), 400
    if not is_chapter and not content: # Content is required for pages
        return jsonify({'message': 'Content is required for pages'}), 400
    if is_chapter and slug: # Chapters should not have slugs
        return jsonify({'message': 'Chapters should not have slugs'}), 400
    if is_chapter and content: # Chapters should not have content
        return jsonify({'message': 'Chapters should not have content directly'}), 400

    pages = read_pages_data()
    # Check for duplicate slug only if it's a page
    if slug and any(p.get('slug') == slug for p in flatten_sidebar(pages)):
        return jsonify({'message': 'Slug already exists. Please choose a unique slug.'}), 409
    content = data.get('content', '')
    published = data.get('published', False)
    is_chapter = data.get('is_chapter', False)
    parent_id = data.get('parent_id')
    design = data.get('design', {})
    meta_description = data.get('meta_description', '')
    meta_keywords = data.get('meta_keywords', '')
    custom_css = data.get('custom_css', '')

    if not title or (not is_chapter and not slug): # Slug is not required for chapters
        return jsonify({'message': 'Title and slug (for pages) are required'}), 400
    if not is_chapter and not content: # Content is required for pages
        return jsonify({'message': 'Content is required for pages'}), 400
    if is_chapter and slug: # Chapters should not have slugs
        return jsonify({'message': 'Chapters should not have slugs'}), 400
    if is_chapter and content: # Chapters should not have content
        return jsonify({'message': 'Chapters should not have content directly'}), 400

    pages = read_pages_data()
    # Check for duplicate slug only if it's a page
    if slug and any(p.get('slug') == slug for p in flatten_sidebar(pages)):
        return jsonify({'message': 'Slug already exists. Please choose a unique slug.'}), 409

    pages = read_pages_data()
    # Check for duplicate slug
    if any(p.get('slug') == slug for p in flatten_sidebar(pages)):
        return jsonify({'message': 'Slug already exists. Please choose a unique slug.'}), 409

    new_item = {
        'id': str(uuid.uuid4()), # Generate unique ID
        'title': title,
        'slug': slug if not is_chapter else None, # Chapters don't have slugs
        'content': content if not is_chapter else None, # Chapters don't have content
        'published': published,
        'design': design,
        'meta_description': meta_description,
        'meta_keywords': meta_keywords,
        'custom_css': custom_css
    }
    if is_chapter:
        new_item['children'] = [] # Initialize children list for chapters
        new_item['slug'] = None # Ensure chapters don't have slugs
        new_item['content'] = None # Ensure chapters don't have content

    if parent_id:
        parent_item = find_item_in_sidebar(pages, parent_id)
        if parent_item and 'children' in parent_item:
            parent_item['children'].append(new_item)
        else:
            return jsonify({'message': 'Parent not found or is not a chapter'}), 400
    else:
        pages.append(new_item)

    write_pages_data(pages)
    return jsonify({'message': 'Page/Chapter added successfully', 'page_id': new_item['id']}), 201

@app.route('/api/admin/pages/<slug>', methods=['PUT'])
@token_required
def edit_page(slug):
    """
    PUT /api/admin/pages/<slug>
    Edits an existing page by its slug. Requires authentication.
    """
    data = request.get_json()
    pages = read_pages_data()

    # Find the page by its slug
    all_pages = flatten_sidebar(pages)
    page_to_edit = next((p for p in all_pages if p.get('slug') == slug), None)

    if not page_to_edit:
        return jsonify({'message': 'Page not found'}), 404

    # Update fields
    page_to_edit['title'] = data.get('title', page_to_edit['title'])
    # Allow slug change, but check for duplicates if changed
    new_slug = data.get('slug', page_to_edit['slug'])
    if new_slug != page_to_edit['slug']:
        if any(p.get('slug') == new_slug and p['id'] != page_to_edit['id'] for p in all_pages):
            return jsonify({'message': 'New slug already exists. Please choose a unique slug.'}), 409
        page_to_edit['slug'] = new_slug

    page_to_edit['content'] = data.get('content', page_to_edit['content'])
    page_to_edit['image'] = data.get('image', page_to_edit.get('image'))
    page_to_edit['video'] = data.get('video', page_to_edit.get('video'))
    page_to_edit['published'] = data.get('published', page_to_edit['published'])
    page_to_edit['design'] = data.get('design', page_to_edit.get('design', {}))
    page_to_edit['meta_description'] = data.get('meta_description', page_to_edit.get('meta_description', ''))
    page_to_edit['meta_keywords'] = data.get('meta_keywords', page_to_edit.get('meta_keywords', ''))
    page_to_edit['custom_css'] = data.get('custom_css', page_to_edit.get('custom_css', ''))

    # Update the nested structure
    update_item_in_sidebar(pages, page_to_edit) # This will update the actual item in the nested list

    write_pages_data(pages)
    return jsonify({'message': 'Page updated successfully'}), 200

@app.route('/api/admin/pages/<slug>', methods=['DELETE'])
@token_required
def delete_page(slug):
    """
    DELETE /api/admin/pages/<slug>
    Deletes a page by its slug. Requires authentication.
    """
    pages = read_pages_data()
    all_pages = flatten_sidebar(pages)
    page_to_delete = next((p for p in all_pages if p.get('slug') == slug), None)

    if not page_to_delete:
        return jsonify({'message': 'Page not found'}), 404

    # Find its parent and remove it
    parent_item = find_parent_of_item(pages, page_to_delete['id'])
    if parent_item:
        remove_item_from_sidebar(parent_item['children'], page_to_delete['id'])
    else:
        remove_item_from_sidebar(pages, page_to_delete['id'])

    write_pages_data(pages)
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

    pages = read_pages_data()
    page_to_update = find_item_in_sidebar(pages, page_id)

    if not page_to_update:
        return jsonify({'message': 'Page not found'}), 404

    page_to_update['published'] = published_status
    write_pages_data(pages)
    return jsonify({'message': 'Page visibility updated successfully', 'published': published_status}), 200

@app.route('/api/admin/sidebar/reorder', methods=['PUT'])
@token_required
def reorder_sidebar():
    """
    PUT /api/admin/sidebar/reorder
    Reorders the sidebar structure based on the provided new order. Requires authentication.
    """
    data = request.get_json()
    new_order = data.get('sidebar_order')

    if not new_order or not isinstance(new_order, list):
        return jsonify({'message': 'Invalid sidebar order provided'}), 400

    current_sidebar = read_pages_data()
    updated_sidebar = reorder_sidebar_structure(current_sidebar, new_order)

    write_pages_data(pager)
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

    pages = read_pages_data()
    page_to_update = find_item_in_sidebar(pages, page_id)

    if not page_to_update:
        return jsonify({'message': 'Page not found'}), 404

    if 'design' not in page_to_update:
        page_to_update['design'] = {}

    if header_color is not None:
        page_to_update['design']['headerColor'] = header_color
    if header_image is not None:
        page_to_update['design']['headerImage'] = header_image

    write_pages_data(pages)
    return jsonify({'message': 'Page design updated successfully', 'design': page_to_update['design']}), 200


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

# --- Run the Flask app ---
if __name__ == '__main__':
    # This is for development only. In production, use a WSGI server like Gunicorn.
    app.run(debug=True, port=5000)
