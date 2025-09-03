import os
import json
from jinja2 import Environment, FileSystemLoader

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
PAGES_FILE = os.path.join(DATA_DIR, 'pages.json')
TEMPLATES_DIR = os.path.join(BASE_DIR, '..', 'public', 'templates')
STATIC_PAGES_DIR = os.path.join(BASE_DIR, '..', 'public', 'pages')
STATIC_ASSETS_PREFIX = '/public' # Prefix for CSS, JS, images

# Ensure static pages directory exists
os.makedirs(STATIC_PAGES_DIR, exist_ok=True)

# Setup Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def read_pages_data():
    """Reads the pages data from the JSON file."""
    if not os.path.exists(PAGES_FILE):
        return []
    with open(PAGES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Normalize content image src paths to include '/public'
        def update_image_paths(items):
            for item in items:
                if isinstance(item, dict):
                    # Drop headerImage if present; no longer used
                    if 'design' in item and isinstance(item['design'], dict):
                        item['design'].pop('headerImage', None)
                    if 'content' in item and isinstance(item['content'], str):
                        # Replace src="/uploads with src="/public/uploads
                        item['content'] = item['content'].replace('src="/uploads', f'src="{STATIC_ASSETS_PREFIX}/uploads')
                    for key, value in item.items():
                        if isinstance(value, list):
                            update_image_paths(value)
        update_image_paths(data)
        return data

def flatten_sidebar(items):
    """Flattens the nested sidebar structure into a single list."""
    flat_list = []
    for item in items:
        flat_list.append(item)
        if 'children' in item and item['children']:
            flat_list.extend(flatten_sidebar(item['children']))
    return flat_list

def generate_sidebar_html(pages_data, current_slug=None):
    """Generates the HTML for the sidebar navigation."""
    html = []
    for item in pages_data:
        if not item.get('published', False):
            continue

        item_slug = item.get('slug')
        has_children = 'children' in item and item['children']

        link_class = "menu-link"
        if item_slug and item_slug == current_slug:
            link_class += " active"

        if has_children:
            # Determine if any child is the current page or contains the current page
            is_expanded = False
            if current_slug:
                flat_children = flatten_sidebar(item['children'])
                if any(child.get('slug') == current_slug for child in flat_children):
                    is_expanded = True

            item_class = "menu-item has-children"
            if is_expanded:
                item_class += " expanded"

            html.append(f'<div class="{item_class}">')
            html.append(f'<a href="#" class="{link_class}" aria-expanded="{"true" if is_expanded else "false"}">{item["title"]}</a>')
            html.append('<ul class="submenu">')
            html.append(generate_sidebar_html(item['children'], current_slug))
            html.append('</ul>')
            html.append('</div>')
        else:
            if item_slug:
                html.append(f'<div class="menu-item">')
                html.append(f'<a href="/pages/{item_slug}.html" class="{link_class}">{item["title"]}</a>')
                html.append(f'</div>')
    return "\n".join(html)

def get_breadcrumbs(pages_data, current_slug):
    """Generates breadcrumbs for a given slug."""
    breadcrumbs = []
    
    def find_path(items, target_slug, current_path):
        for item in items:
            if item.get('slug') == target_slug:
                return current_path + [{'title': item['title'], 'url': f'/pages/{item["slug"]}.html'}]
            if 'children' in item and item['children']:
                path = find_path(item['children'], target_slug, current_path + [{'title': item['title'], 'url': f'/pages/{item["slug"]}.html' if item.get('slug') else '#'}])
                if path:
                    return path
        return None

    # Start with a home link
    breadcrumbs.append({'title': 'Home', 'url': '/index.html'})

    path = find_path(pages_data, current_slug, [])
    if path:
        breadcrumbs.extend(path)
    
    return breadcrumbs

def generate_static_pages():
    pages_data = read_pages_data()
    all_pages = flatten_sidebar(pages_data)
    page_template = env.get_template('page.html')
    
    # Generate index.html (the welcome page)
    index_template = env.get_template('base.html')
    index_sidebar_html = generate_sidebar_html(pages_data)
    index_html_content = index_template.render(
        page={'title': 'Welcome to Somabay Handbook', 'meta_description': 'Somabay Handbook provides comprehensive information about our company, destination, benefits, and policies.'},
        sidebar_menu=index_sidebar_html,
        breadcrumbs=[{'title': 'Home', 'url': '/index.html'}]
    )
    with open(os.path.join(STATIC_PAGES_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html_content)
    print(f"Generated: {os.path.join(STATIC_PAGES_DIR, 'index.html')}")

    for page in all_pages:
        if page.get('slug') and page.get('content') and page.get('published', False):
            slug = page['slug']
            output_path = os.path.join(STATIC_PAGES_DIR, f'{slug}.html')
            
            sidebar_html = generate_sidebar_html(pages_data, current_slug=slug)
            breadcrumbs = get_breadcrumbs(pages_data, slug)

            rendered_html = page_template.render(
                page=page,
                sidebar_menu=sidebar_html,
                breadcrumbs=breadcrumbs
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            print(f"Generated: {output_path}")

if __name__ == '__main__':
    generate_static_pages()
