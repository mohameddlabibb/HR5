# Somabay Handbook Website Project

This project provides a full-stack handbook website for Somabay, featuring a left sidebar navigation and an admin panel for content management.

# Somabay Handbook Website Project

This project provides a full-stack handbook website for Somabay, featuring a left sidebar navigation and an admin panel for content management.

## Project Structure

```
.
├── README.md
├── package.json
├── server.js
├── public
│   ├── index.html
│   ├── admin.html
│   ├── css
│   │   └── main.css
│   ├── js
│   │   └── app.js
│   │   └── admin.js
│   └── uploads
│       └── placeholder-image.jpg
├── backend
│   ├── app.py
│   ├── requirements.txt
│   ├── config.py
│   ├── database.py
│   └── site.db  (SQLite database file)
└── data
    └── pages.json
```

## Technologies Used

*   **Frontend:** HTML, CSS, JavaScript, JSON, Node.js (as a static server), Bootstrap 5, jQuery UI (for sortable lists)
*   **Backend:** Python (Flask framework), SQLite3 (database)
*   **Authentication:** Werkzeug Security (for password hashing)

## Setup and Running Instructions

Follow these steps to set up and run the project locally in VS Code.

### 1. VS Code Extensions (Recommended)

For a better development experience, consider installing these VS Code extensions:
*   **Python:** For Python language support, debugging, and virtual environment management.
*   **ESLint:** For JavaScript linting.
*   **Prettier:** For code formatting (JavaScript, HTML, CSS, JSON).

### 2. Node.js Frontend Setup

1.  **Install Node.js Dependencies:**
    Navigate to the project root directory (`e:/HR5`) in your terminal and run:
    ```bash
    npm install
    ```
    This will install `express` (for the static server) and `concurrently` (to run both frontend and backend servers simultaneously).

### 3. Python Backend Setup

1.  **Create a Python Virtual Environment:**
    In the project root directory, run:
    ```bash
    python -m venv venv
    ```
    This creates a virtual environment named `venv` to manage Python dependencies.

2.  **Activate the Virtual Environment:**
    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    You should see `(venv)` at the beginning of your terminal prompt, indicating the virtual environment is active.

3.  **Install Python Dependencies:**
    With the virtual environment activated, install the required Python packages:
    ```bash
    pip install -r backend/requirements.txt
    ```
    This installs `Flask` (the web framework), `Flask-Cors` (for CORS handling), and `Werkzeug` (for password hashing).

### 4. Database Initialization and Admin User Creation

The project uses SQLite for its database (`site.db`). The `backend/database.py` script is responsible for creating the necessary tables (`users`, `settings`, `menus`, `widgets`) and an initial admin user.

1.  **Initialize Database and Create Admin:**
    With your Python virtual environment activated, run the `database.py` script:
    ```bash
    python backend/database.py
    ```
    This will create `site.db` (if it doesn't exist), set up the tables, and create a default admin user with username `admin` and password `password`. **Remember to change this default password immediately in a production environment!**

### 5. Running the Servers

You have two options to run the frontend (Node.js static server) and backend (Python Flask API):

#### Option 1: Concurrent Run (Recommended)

This option uses `concurrently` to start both servers with a single command.

1.  **In the project root**, run:
    ```bash
    npm run dev
    ```
    *   The Node.js static server will typically run on `http://localhost:3001`.
    *   The Flask backend API server will typically run on `http://localhost:5000`.
    *   The terminal will show output from both servers.

#### Option 2: Separate Terminals

If you prefer to manage each server independently:

1.  **Terminal 1 (Frontend Static Server):**
    *   In the project root, run:
        ```bash
        npm start
        ```
        This starts the Node.js server, serving static files from `public/` on `http://localhost:3001`.

2.  **Terminal 2 (Python Backend API Server):**
    *   Activate your Python virtual environment:
        *   Windows: `.\venv\Scripts\activate`
        *   macOS/Linux: `source venv/bin/activate`
    *   Navigate to the `backend` directory:
        ```bash
        cd backend
        ```
    *   Run the Flask application:
        ```bash
        flask run
        ```
        This starts the Flask API server on `http://localhost:5000`.

## Frontend-Backend Communication

The frontend JavaScript (`public/js/app.js` and `public/js/admin.js`) communicates with the Flask backend API using `fetch` requests. For example, to get sidebar data, it will call `GET /api/sidebar`.

**CORS (Cross-Origin Resource Sharing):** The `backend/app.py` includes CORS configuration to allow requests from the Node.js static server's origin (`http://localhost:3001`) to prevent browser security errors.

## Accessing the Application

*   **Handbook Website:** Open your browser and go to `http://localhost:3001`.
*   **Admin Panel:** Open your browser and go to `http://localhost:3001/admin`.

## Admin Panel Features and Usage

The admin panel provides a comprehensive interface for managing the Somabay Handbook website.

**Default Admin Credentials for Testing:**
*   **Username:** `admin`
*   **Password:** `password`
    *(Highly recommended to change this in a production environment!)*

Once logged in, you can use the admin interface to:

*   **Page Management:**
    *   Add new pages or chapters (chapters can contain sub-pages).
    *   Edit existing page titles, slugs, content, images, and videos.
    *   New fields for pages include: `Meta Description`, `Meta Keywords`, and `Custom CSS` for advanced SEO and styling.
    *   Remove pages.
    *   Reorder items in the sidebar using drag-and-drop.
    *   Toggle page visibility (published/draft).
    *   Change page header color and header image.
*   **Menu Builder:**
    *   Create multiple navigation menus for different parts of your site.
    *   Add, edit, reorder, and delete menu items (each with a title, URL, and target).
*   **Widget System:**
    *   Create and manage various types of widgets (e.g., Text/HTML, Image, Social Links).
    *   Widgets can be configured with specific content based on their type.
*   **CMS Settings:**
    *   Configure global website settings such as `Site Title`, `Footer Text`, and `Social Media Links` (Facebook, Twitter).
*   **Image Uploads:**
    *   Upload images directly through the admin panel (these will be stored in `public/uploads/`).

All changes made through the admin panel are persisted in the `site.db` SQLite database and `data/pages.json` file.

## Editing Content and UI

### Handbook Content (`data/pages.json` and `site.db`)

*   `data/pages.json` stores all your handbook pages and the sidebar structure.
*   `site.db` stores CMS settings, menus, and widgets.
*   You can directly inspect these files for advanced debugging or bulk changes, but the admin panel is designed for easier management.

### Frontend UI (`public/`)

*   **HTML:** `public/index.html` (main site) and `public/admin.html` (admin panel) define the page structures.
*   **CSS:** `public/css/main.css` contains all custom styles.
*   **JavaScript:**
    *   `public/js/app.js` handles client-side routing, sidebar rendering, and content display for the main site.
    *   `public/js/admin.js` handles admin panel logic, form submissions, and API interactions.

### Responsive UI

The frontend is built with Bootstrap 5, ensuring a responsive design that adapts to various screen sizes and devices. New UI elements for the admin panel features (CMS settings, menu builder, widget system) have been implemented with responsiveness in mind.

## Extending Features

*   **New API Endpoints:** Add new routes and functions to `backend/app.py` to extend backend functionality.
*   **New Frontend Components:** Create new HTML sections, CSS classes, and JavaScript functions/modules in the `public/` directory to add new UI elements or features.
*   **Authentication:** For production environments, consider replacing the simple token-based authentication with a more robust solution like JWT (JSON Web Tokens) or OAuth. Secure your `config.py` file or use environment variables for sensitive data.
*   **New Widget Types:** Extend the `renderWidgetDataFields` and `getWidgetDataFromForm` functions in `public/js/admin.js` and the `create_widget`/`update_widget` logic in `backend/app.py` to support additional widget types.
*   **Frontend Integration:** To display menus and widgets on the public-facing site (`public/index.html`), you would need to implement logic in `public/js/app.js` to fetch data from `/api/menus/<name>` and `/api/widgets/<name>` and render them dynamically.
