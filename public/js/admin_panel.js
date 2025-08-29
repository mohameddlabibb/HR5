// public/js/admin_panel.js
// Client-side JavaScript for the Somabay Handbook Admin Panel dashboard.
// Handles page management (CRUD), sidebar reordering, image uploads, and design options.

document.addEventListener('DOMContentLoaded', () => {
    const adminDashboardSection = document.getElementById('admin-dashboard');
    const logoutButton = document.getElementById('logout-button');

    const addPageForm = document.getElementById('add-page-form');
    const editPageForm = document.getElementById('edit-page-form');
    const deletePageButton = document.getElementById('delete-page-button');
    const addPageParentSelect = document.getElementById('add-page-parent');
    const pagesList = document.getElementById('pages-list');
    const sidebarSortable = document.getElementById('sidebar-sortable');
    const saveSidebarOrderButton = document.getElementById('save-sidebar-order');
    const imageUploadForm = document.getElementById('image-upload-form');
    const uploadMessage = document.getElementById('upload-message');

    // CMS Settings elements
    const cmsSettingsTab = document.getElementById('settings-tab');
    const cmsSettingsContent = document.getElementById('settings'); // The tab-pane div

    // Menu Builder elements
    const menusList = document.getElementById('menus-list');
    const addMenuForm = document.getElementById('add-menu-form');
    const addMenuMessage = document.getElementById('add-menu-message');
    const menuEditorArea = document.getElementById('menu-editor-area');
    const currentMenuName = document.getElementById('current-menu-name');
    const addMenuItemButton = document.getElementById('add-menu-item-button');
    const menuItemsSortable = document.getElementById('menu-items-sortable');
    const saveMenuItemsOrderButton = document.getElementById('save-menu-items-order');
    const cancelMenuEditButton = document.getElementById('cancel-menu-edit');
    const menuItemForm = document.getElementById('menu-item-form');
    const menuItemModalLabel = document.getElementById('menuItemModalLabel');
    let currentEditingMenu = null; // Stores the menu object being edited

    // Widget System elements
    const widgetsList = document.getElementById('widgets-list');
    const addWidgetForm = document.getElementById('add-widget-form');
    const addWidgetMessage = document.getElementById('add-widget-message');
    const newWidgetTypeSelect = document.getElementById('new-widget-type');
    const newWidgetDataContainer = document.getElementById('new-widget-data-container');
    const editWidgetForm = document.getElementById('edit-widget-form');
    const editWidgetNameHidden = document.getElementById('edit-widget-name-hidden');
    const editWidgetNameInput = document.getElementById('edit-widget-name');
    const editWidgetTypeSelect = document.getElementById('edit-widget-type');
    const editWidgetDataContainer = document.getElementById('edit-widget-data-container');
    const deleteWidgetButton = document.getElementById('delete-widget-button');
    let currentEditingWidget = null; // Stores the widget object being edited

    let adminToken = localStorage.getItem('adminToken'); // Retrieve token from local storage

    // --- Utility Functions ---

    /**
     * Displays a message to the user.
     * @param {HTMLElement} element - The DOM element to display the message in.
     * @param {string} message - The message text.
     * @param {boolean} isError - True if it's an error message, false otherwise.
     */
    function showMessage(element, message, isError = false) {
        // For admin_panel, we'll use alert for now as there's no dedicated message element
        if (isError) {
            alert(`Error: ${message}`);
        } else {
            alert(message);
        }
    }

    /**
     * Checks if the user is authenticated.
     * @returns {boolean} True if a token exists, false otherwise.
     */
    function isAuthenticated() {
        return !!adminToken;
    }

    /**
     * Sets the authorization header for API requests.
     * @returns {Object} Headers object.
     */
    function getAuthHeaders() {
        const token = localStorage.getItem('adminToken');
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };
    }

    /**
     * Recursively flattens the sidebar structure into a single array of pages.
     * @param {Array} items - The sidebar items.
     * @param {Array} flatList - The accumulator for the flattened list.
     * @param {string|null} parentId - The ID of the parent item.
     * @returns {Array} The flattened list of pages.
     */
    function flattenSidebar(items, flatList = [], parentId = null) {
        items.forEach(item => {
            flatList.push({ ...item, parentId: parentId });
            if (item.children) {
                flattenSidebar(item.children, flatList, item.id);
            }
        });
        return flatList;
    }

    /**
     * Recursively finds a page by its ID in the sidebar structure.
     * @param {Array} items - The sidebar items.
     * @param {string} id - The ID of the page to find.
     * @returns {Object|null} The found page object or null.
     */
    function findPageById(items, id) {
        for (const item of items) {
            if (item.id === id) {
                return item;
            }
            if (item.children) {
                const found = findPageById(item.children, id);
                if (found) return found;
            }
        }
        return null;
    }

    /**
     * Handles admin logout.
     */
    logoutButton.addEventListener('click', () => {
        adminToken = null;
        localStorage.removeItem('adminToken');
        window.location.href = '/admin.html'; // Redirect to login page
    });

    /**
     * Shows the admin dashboard.
     */
    function showAdminDashboard() {
        console.log('Showing admin dashboard'); // Debugging
        adminDashboardSection.style.display = 'block';
        loadAdminData(); // Load pages and sidebar structure
        // Initialize Bootstrap tabs
        const adminTab = new bootstrap.Tab(document.getElementById('pages-tab'));
        adminTab.show();
    }

    // --- Data Loading and Rendering ---

    /**
     * Loads all necessary data for the admin dashboard (pages and sidebar).
     */
    async function loadAdminData() {
        await fetchPagesList();
        await fetchSidebarForAdmin();
        populateParentOptions();
        // Load CMS settings when dashboard is shown
        await fetchCMSSettings();
    }

    /**
     * Fetches all pages and renders them in the dashboard.
     */
    async function fetchPagesList() {
        try {
            const response = await fetch('/api/sidebar', { headers: getAuthHeaders() });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const sidebar = await response.json();
            const allPages = flattenSidebar(sidebar); // Get a flat list of all pages
            renderPagesList(allPages);
        } catch (error) {
            console.error('Error fetching pages list:', error);
            pagesList.innerHTML = '<p class="text-danger">Failed to load pages.</p>';
            if (error.message.includes('401')) {
                alert('Session expired. Please log in again.'); // Use alert for now
                logoutButton.click(); // Force logout on unauthorized
            }
        }
    }

    /**
     * Renders the list of all pages in the dashboard.
     * @param {Array} pages - The array of page objects.
     */
    function renderPagesList(pages) {
        pagesList.innerHTML = '';
        if (pages.length === 0) {
            pagesList.innerHTML = '<p>No pages found. Add a new page.</p>';
            return;
        }

        const ul = document.createElement('ul');
        ul.classList.add('list-group');

        pages.forEach(page => {
            const li = document.createElement('li');
            li.classList.add('list-group-item');
            li.innerHTML = `
                <span>${page.title} (${page.slug}) - ${page.published ? 'Published' : 'Draft'}</span>
                <div class="page-actions">
                    <button class="btn btn-sm btn-info edit-page-btn" data-id="${page.id}">Edit</button>
                    <button class="btn btn-sm btn-${page.published ? 'secondary' : 'success'} toggle-visibility-btn" data-id="${page.id}" data-published="${page.published}">
                        ${page.published ? 'Set Draft' : 'Publish'}
                    </button>
                </div>
            `;
            ul.appendChild(li);
        });
        pagesList.appendChild(ul);

        // Add event listeners for edit and toggle visibility buttons
        document.querySelectorAll('.edit-page-btn').forEach(button => {
            button.addEventListener('click', (e) => openEditPageModal(e.target.dataset.id));
        });
        document.querySelectorAll('.toggle-visibility-btn').forEach(button => {
            button.addEventListener('click', (e) => togglePageVisibility(e.target.dataset.id, e.target.dataset.published === 'true'));
        });
    }

    /**
     * Fetches the sidebar structure and renders it as a sortable list for admin.
     */
    async function fetchSidebarForAdmin() {
        try {
            const response = await fetch('/api/sidebar', { headers: getAuthHeaders() });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const sidebar = await response.json();
            renderSortableSidebar(sidebar, sidebarSortable);
            // Initialize jQuery UI Sortable
            $(sidebarSortable).sortable({
                axis: 'y',
                handle: '.drag-handle',
                placeholder: 'ui-state-highlight',
                forcePlaceholderSize: true,
                opacity: 0.8,
                update: function(event, ui) {
                    // Optional: provide visual feedback or log order change
                    console.log('Sidebar order changed.');
                }
            });
            $(sidebarSortable).disableSelection(); // Prevent text selection during drag
        } catch (error) {
            console.error('Error fetching sidebar for admin:', error);
            sidebarSortable.innerHTML = '<p class="text-danger">Failed to load sidebar structure.</p>';
        }
    }

    /**
     * Recursively renders the sidebar as a sortable list for the admin panel.
     * @param {Array} items - The sidebar items.
     * @param {HTMLElement} parentElement - The DOM element to append to.
     */
    function renderSortableSidebar(items, parentElement) {
        parentElement.innerHTML = ''; // Clear existing
        items.forEach(item => {
            const li = document.createElement('li');
            li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
            li.dataset.id = item.id; // Store ID for reordering

            const itemContent = document.createElement('div');
            itemContent.innerHTML = `
                <span class="drag-handle me-2" style="cursor: grab;">&#x2261;</span>
                <span>${item.title} (${item.slug || 'Chapter'})</span>
            `;
            li.appendChild(itemContent);

            const actions = document.createElement('div');
            const editButton = document.createElement('button');
            editButton.classList.add('btn', 'btn-sm', 'btn-info', 'ms-2');
            editButton.textContent = 'Edit';
            editButton.addEventListener('click', () => openEditPageModal(item.id));
            actions.appendChild(editButton);
            li.appendChild(actions);

            parentElement.appendChild(li);

            if (item.children && item.children.length > 0) {
                const nestedUl = document.createElement('ul');
                nestedUl.classList.add('list-group', 'mt-2', 'ms-4'); // Indent nested items
                // Make nested lists sortable too
                $(nestedUl).sortable({
                    axis: 'y',
                    handle: '.drag-handle',
                    placeholder: 'ui-state-highlight',
                    forcePlaceholderSize: true,
                    opacity: 0.8,
                    update: function(event, ui) {
                        console.log('Nested sidebar order changed.');
                    }
                });
                $(nestedUl).disableSelection();
                renderSortableSidebar(item.children, nestedUl);
                li.appendChild(nestedUl);
            }
        });
    }

    /**
     * Populates the parent chapter dropdown for adding new pages.
     */
    async function populateParentOptions() {
        try {
            const response = await fetch('/api/sidebar', { headers: getAuthHeaders() });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const sidebar = await response.json();
            addPageParentSelect.innerHTML = '<option value="">-- No Parent (Top Level) --</option>';
            // Recursively add chapters to the dropdown
            function addChaptersToSelect(items, indent = '') {
                items.forEach(item => {
                    if (item.children) { // Only chapters can be parents
                        const option = document.createElement('option');
                        option.value = item.id;
                        option.textContent = `${indent}${item.title} (Chapter)`;
                        addPageParentSelect.appendChild(option);
                        addChaptersToSelect(item.children, indent + '-- ');
                    }
                });
            }
            addChaptersToSelect(sidebar);
        } catch (error) {
            console.error('Error populating parent options:', error);
        }
    }

    // --- Page Management (Add, Edit, Delete, Toggle Visibility) ---

    /**
     * Handles adding a new page or chapter.
     * @param {Event} e - The form submission event.
     */
    addPageForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const newPage = {
            title: document.getElementById('add-page-title').value,
            slug: document.getElementById('add-page-slug').value,
            content: document.getElementById('add-page-content').value,
            published: document.getElementById('add-page-published').checked,
            is_chapter: document.getElementById('add-page-is-chapter').checked,
            parent_id: document.getElementById('add-page-parent').value || null,
            design: {
                headerColor: document.getElementById('add-page-header-color').value,
                headerImage: document.getElementById('add-page-header-image').value
            },
            meta_description: document.getElementById('add-page-meta-description').value,
            meta_keywords: document.getElementById('add-page-meta-keywords').value,
            custom_css: document.getElementById('add-page-custom-css').value
        };

        // Basic validation
        if (!newPage.title || (newPage.is_chapter === false && !newPage.slug)) {
            alert('Title and Slug (for pages) are required.');
            return;
        }
        if (newPage.is_chapter && newPage.content) {
            alert('Chapters should not have content directly. Content should be in sub-pages.');
            return;
        }
        if (!newPage.is_chapter && !newPage.content) {
            alert('Pages must have content.');
            return;
        }
        if (newPage.is_chapter && newPage.slug) {
            alert('Chapters should not have slugs.');
            return;
        }

        try {
            const response = await fetch('/api/admin/pages', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(newPage)
            });

            const data = await response.json();
            console.log('Add page API response:', data); // Log the full response

            if (response.ok) {
                alert('Page/Chapter added successfully!');
                $('#addPageModal').modal('hide'); // Hide modal
                addPageForm.reset(); // Clear form
                loadAdminData(); // Reload dashboard data
            } else {
                alert(data.message || 'Failed to add page/chapter. Check console for details.');
            }
        } catch (error) {
            console.error('Error adding page:', error);
            alert('An error occurred while adding the page/chapter. Check console for details.');
        }
    });

    /**
     * Opens the edit page modal and populates it with existing page data.
     * @param {string} pageId - The ID of the page to edit.
     */
    async function openEditPageModal(pageId) {
        try {
            const response = await fetch('/api/sidebar', { headers: getAuthHeaders() });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const sidebar = await response.json();
            const pageToEdit = findPageById(sidebar, pageId);

            if (pageToEdit) {
                document.getElementById('edit-page-id').value = pageToEdit.id;
                document.getElementById('edit-page-title').value = pageToEdit.title;
                document.getElementById('edit-page-slug').value = pageToEdit.slug || '';
                document.getElementById('edit-page-content').value = pageToEdit.content || '';
                document.getElementById('edit-page-image').value = pageToEdit.image || '';
                document.getElementById('edit-page-video').value = pageToEdit.video || '';
                document.getElementById('edit-page-published').checked = pageToEdit.published;
                document.getElementById('edit-page-header-color').value = pageToEdit.design?.headerColor || '#f8f9fa';
                document.getElementById('edit-page-header-image').value = pageToEdit.design?.headerImage || '';
                document.getElementById('edit-page-meta-description').value = pageToEdit.meta_description || '';
                document.getElementById('edit-page-meta-keywords').value = pageToEdit.meta_keywords || '';
                document.getElementById('edit-page-custom-css').value = pageToEdit.custom_css || '';

                $('#editPageModal').modal('show');
            } else {
                alert('Page not found.');
            }
        } catch (error) {
            console.error('Error opening edit modal:', error);
            alert('Failed to load page data for editing.');
        }
    }

    /**
     * Handles editing an existing page.
     * @param {Event} e - The form submission event.
     */
    editPageForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const pageId = document.getElementById('edit-page-id').value;
        const updatedPage = {
            title: document.getElementById('edit-page-title').value,
            slug: document.getElementById('edit-page-slug').value,
            content: document.getElementById('edit-page-content').value,
            image: document.getElementById('edit-page-image').value,
            video: document.getElementById('edit-page-video').value,
            published: document.getElementById('edit-page-published').checked,
            design: {
                headerColor: document.getElementById('edit-page-header-color').value,
                headerImage: document.getElementById('edit-page-header-image').value
            },
            meta_description: document.getElementById('edit-page-meta-description').value,
            meta_keywords: document.getElementById('edit-page-meta-keywords').value,
            custom_css: document.getElementById('edit-page-custom-css').value
        };

        // Basic validation
        if (!updatedPage.title || !updatedPage.slug) {
            alert('Title and Slug are required.');
            return;
        }

        try {
            const response = await fetch(`/api/admin/pages/${updatedPage.slug}`, {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify(updatedPage)
            });

            const data = await response.json();

            if (response.ok) {
                alert('Page updated successfully!');
                $('#editPageModal').modal('hide');
                loadAdminData();
            } else {
                alert(data.message || 'Failed to update page.');
            }
        } catch (error) {
            console.error('Error updating page:', error);
            alert('An error occurred while updating the page.');
        }
    });

    /**
     * Handles deleting a page.
     */
    deletePageButton.addEventListener('click', async () => {
        const pageId = document.getElementById('edit-page-id').value;
        const pageSlug = document.getElementById('edit-page-slug').value; // Need slug for DELETE endpoint

        if (!confirm(`Are you sure you want to delete the page "${document.getElementById('edit-page-title').value}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/pages/${pageSlug}`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });

            const data = await response.json();

            if (response.ok) {
                alert('Page deleted successfully!');
                $('#editPageModal').modal('hide');
                loadAdminData();
            } else {
                alert(data.message || 'Failed to delete page.');
            }
        } catch (error) {
            console.error('Error deleting page:', error);
            alert('An error occurred while deleting the page.');
        }
    });

    /**
     * Toggles the published status of a page.
     * @param {string} pageId - The ID of the page.
     * @param {boolean} currentPublishedStatus - The current published status.
     */
    async function togglePageVisibility(pageId, currentPublishedStatus) {
        const newStatus = !currentPublishedStatus;
        if (!confirm(`Are you sure you want to ${newStatus ? 'publish' : 'draft'} this page?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/pages/${pageId}/visibility`, {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify({ published: newStatus })
            });

            const data = await response.json();

            if (response.ok) {
                alert(`Page visibility updated to ${newStatus ? 'Published' : 'Draft'}.`);
                loadAdminData();
            } else {
                alert(data.message || 'Failed to update page visibility.');
            }
        } catch (error) {
            console.error('Error toggling visibility:', error);
            alert('An error occurred while updating page visibility.');
        }
    }

    // --- Sidebar Reordering ---

    /**
     * Saves the new order of sidebar items.
     */
    saveSidebarOrderButton.addEventListener('click', async () => {
        // Function to get the current order of items recursively
        function getCurrentOrder(parentElement) {
            const order = [];
            $(parentElement).children('li').each(function() {
                const itemId = $(this).data('id');
                const childrenUl = $(this).children('ul');
                const item = { id: itemId };
                if (childrenUl.length > 0) {
                    item.children = getCurrentOrder(childrenUl);
                }
                order.push(item);
            });
            return order;
        }

        const newSidebarOrder = getCurrentOrder(sidebarSortable);

        try {
            const response = await fetch('/api/admin/sidebar/reorder', {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify({ sidebar_order: newSidebarOrder })
            });

            const data = await response.json();

            if (response.ok) {
                alert('Sidebar order saved successfully!');
                loadAdminData(); // Reload to reflect changes
            } else {
                alert(data.message || 'Failed to save sidebar order.');
            }
        } catch (error) {
            console.error('Error saving sidebar order:', error);
            alert('An error occurred while saving the sidebar order.');
        }
    });

    // --- CMS Settings Management ---

    /**
     * Fetches and displays CMS settings.
     */
    async function fetchCMSSettings() {
        try {
            const response = await fetch('/api/admin/settings', { headers: getAuthHeaders() });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const settings = await response.json();
            renderCMSSettingsForm(settings);
        } catch (error) {
            console.error('Error fetching CMS settings:', error);
            cmsSettingsContent.innerHTML = '<p class="text-danger">Failed to load CMS settings.</p>';
            if (error.message.includes('401')) {
                alert('Session expired. Please log in again.'); // Use alert for now
                logoutButton.click();
            }
        }
    }

    /**
     * Renders the CMS settings form.
     * @param {Object} settings - The CMS settings object.
     */
    function renderCMSSettingsForm(settings) {
        cmsSettingsContent.innerHTML = `
            <form id="cms-settings-form" class="mt-3">
                <div class="mb-3">
                    <label for="site-title" class="form-label">Site Title</label>
                    <input type="text" class="form-control" id="site-title" value="${settings.site_title || ''}" required>
                </div>
                <div class="mb-3">
                    <label for="footer-text" class="form-label">Footer Text</label>
                    <input type="text" class="form-control" id="footer-text" value="${settings.footer_text || ''}">
                </div>
                <div class="mb-3">
                    <label for="social-facebook" class="form-label">Facebook URL</label>
                    <input type="url" class="form-control" id="social-facebook" value="${settings.social_facebook || ''}">
                </div>
                <div class="mb-3">
                    <label for="social-twitter" class="form-label">Twitter URL</label>
                    <input type="url" class="form-control" id="social-twitter" value="${settings.social_twitter || ''}">
                </div>
                <button type="submit" class="btn btn-primary">Save CMS Settings</button>
                <div id="cms-settings-message" class="mt-3"></div>
            </form>
        `;

        document.getElementById('cms-settings-form').addEventListener('submit', saveCMSSettings);
    }

    /**
     * Handles saving CMS settings.
     * @param {Event} e - The form submission event.
     */
    async function saveCMSSettings(e) {
        e.preventDefault();
        const settingsMessage = document.getElementById('cms-settings-message');

        const updatedSettings = {
            site_title: document.getElementById('site-title').value,
            footer_text: document.getElementById('footer-text').value,
            social_facebook: document.getElementById('social-facebook').value,
            social_twitter: document.getElementById('social-twitter').value,
        };

        try {
            const response = await fetch('/api/admin/settings', {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify(updatedSettings)
            });

            const data = await response.json();

            if (response.ok) {
                showMessage(settingsMessage, 'CMS settings saved successfully!', false);
            } else {
                showMessage(settingsMessage, data.message || 'Failed to save CMS settings.', true);
            }
        } catch (error) {
            console.error('Error saving CMS settings:', error);
            showMessage(settingsMessage, 'An error occurred while saving CMS settings.', true);
        }
    }

    // --- Menu Builder Management ---

    /**
     * Loads all menus and renders them in the dashboard.
     */
    async function loadMenuBuilder() {
        try {
            const response = await fetch('/api/admin/menus', { headers: getAuthHeaders() });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const menus = await response.json();
            renderMenusList(menus);
            menuEditorArea.style.display = 'none'; // Hide editor when loading menu list
        } catch (error) {
            console.error('Error fetching menus:', error);
            menusList.innerHTML = '<p class="text-danger">Failed to load menus.</p>';
            if (error.message.includes('401')) {
                alert('Session expired. Please log in again.'); // Use alert for now
                logoutButton.click();
            }
        }
    }

    /**
     * Renders the list of all menus in the dashboard.
     * @param {Array} menus - The array of menu objects.
     */
    function renderMenusList(menus) {
        menusList.innerHTML = '';
        if (menus.length === 0) {
            menusList.innerHTML = '<p>No menus found. Add a new menu.</p>';
            return;
        }

        const ul = document.createElement('ul');
        ul.classList.add('list-group');

        menus.forEach(menu => {
            const li = document.createElement('li');
            li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
            li.innerHTML = `
                <span>${menu.name}</span>
                <div>
                    <button class="btn btn-sm btn-info edit-menu-btn me-2" data-name="${menu.name}">Edit</button>
                    <button class="btn btn-sm btn-danger delete-menu-btn" data-name="${menu.name}">Delete</button>
                </div>
            `;
            ul.appendChild(li);
        });
        menusList.appendChild(ul);

        document.querySelectorAll('.edit-menu-btn').forEach(button => {
            button.addEventListener('click', (e) => openMenuEditor(e.target.dataset.name));
        });
        document.querySelectorAll('.delete-menu-btn').forEach(button => {
            button.addEventListener('click', (e) => deleteMenu(e.target.dataset.name));
        });
    }

    /**
     * Handles adding a new menu.
     * @param {Event} e - The form submission event.
     */
    addMenuForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const newMenuName = document.getElementById('new-menu-name').value;

        if (!newMenuName) {
            alert('Menu name is required.'); // Use alert for now
            return;
        }

        try {
            const response = await fetch('/api/admin/menus', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ name: newMenuName, menu_data: [] })
            });

            const data = await response.json();

            if (response.ok) {
                alert('Menu created successfully!'); // Use alert for now
                $('#addMenuModal').modal('hide');
                addMenuForm.reset();
                loadMenuBuilder();
            } else {
                alert(data.message || 'Failed to create menu.'); // Use alert for now
            }
        } catch (error) {
            console.error('Error adding menu:', error);
            alert('An error occurred while creating the menu.'); // Use alert for now
        }
    });

    /**
     * Opens the menu editor for a specific menu.
     * @param {string} menuName - The name of the menu to edit.
     */
    async function openMenuEditor(menuName) {
        try {
            const response = await fetch(`/api/admin/menus/${menuName}`, { headers: getAuthHeaders() });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            currentEditingMenu = await response.json();
            currentMenuName.textContent = currentEditingMenu.name;
            renderMenuItems(currentEditingMenu.menu_data);
            menuEditorArea.style.display = 'block';
            menusList.style.display = 'none'; // Hide menu list
            // Initialize jQuery UI Sortable for menu items
            $(menuItemsSortable).sortable({
                axis: 'y',
                handle: '.drag-handle',
                placeholder: 'ui-state-highlight',
                forcePlaceholderSize: true,
                opacity: 0.8,
                update: function(event, ui) {
                    console.log('Menu item order changed.');
                }
            });
            $(menuItemsSortable).disableSelection();
        } catch (error) {
            console.error('Error opening menu editor:', error);
            alert('Failed to load menu for editing.');
        }
    }

    /**
     * Renders the menu items in the sortable list.
     * @param {Array} items - The array of menu items.
     */
    function renderMenuItems(items) {
        menuItemsSortable.innerHTML = '';
        if (items.length === 0) {
            menuItemsSortable.innerHTML = '<li class="list-group-item text-muted">No menu items. Add one!</li>';
            return;
        }

        items.forEach(item => {
            const li = document.createElement('li');
            li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
            li.dataset.id = item.id;
            li.innerHTML = `
                <span class="drag-handle me-2" style="cursor: grab;">&#x2261;</span>
                <span>${item.title}</span>
                <div>
                    <button class="btn btn-sm btn-info edit-menu-item-btn me-2" data-id="${item.id}">Edit</button>
                    <button class="btn btn-sm btn-danger delete-menu-item-btn" data-id="${item.id}">Delete</button>
                </div>
            `;
            menuItemsSortable.appendChild(li);
        });

        document.querySelectorAll('.edit-menu-item-btn').forEach(button => {
            button.addEventListener('click', (e) => openMenuItemModal(e.target.dataset.id));
        });
        document.querySelectorAll('.delete-menu-item-btn').forEach(button => {
            button.addEventListener('click', (e) => deleteMenuItem(e.target.dataset.id));
        });
    }

    /**
     * Opens the add/edit menu item modal.
     * @param {string|null} itemId - The ID of the item to edit, or null for a new item.
     */
    function openMenuItemModal(itemId = null) {
        menuItemForm.reset();
        document.getElementById('menu-item-id').value = itemId || '';
        menuItemModalLabel.textContent = itemId ? 'Edit Menu Item' : 'Add New Menu Item';

        if (itemId && currentEditingMenu) {
            const itemToEdit = currentEditingMenu.menu_data.find(item => item.id === itemId);
            if (itemToEdit) {
                document.getElementById('menu-item-title').value = itemToEdit.title;
                document.getElementById('menu-item-url').value = itemToEdit.url;
                document.getElementById('menu-item-target').value = itemToEdit.target || '_self';
            }
        }
        $('#menuItemModal').modal('show');
    }

    /**
     * Handles saving a menu item (add or edit).
     * @param {Event} e - The form submission event.
     */
    menuItemForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const itemId = document.getElementById('menu-item-id').value;
        const title = document.getElementById('menu-item-title').value;
        const url = document.getElementById('menu-item-url').value;
        const target = document.getElementById('menu-item-target').value;

        if (!title || !url) {
            alert('Title and URL are required for menu items.');
            return;
        }

        const newItem = { id: itemId || String(Date.now()), title, url, target };

        if (currentEditingMenu) {
            if (itemId) {
                // Edit existing item
                const index = currentEditingMenu.menu_data.findIndex(item => item.id === itemId);
                if (index !== -1) {
                    currentEditingMenu.menu_data[index] = newItem;
                }
            } else {
                // Add new item
                currentEditingMenu.menu_data.push(newItem);
            }
            renderMenuItems(currentEditingMenu.menu_data);
            $('#menuItemModal').modal('hide');
        }
    });

    /**
     * Deletes a menu item from the current editing menu.
     * @param {string} itemId - The ID of the item to delete.
     */
    function deleteMenuItem(itemId) {
        if (!confirm('Are you sure you want to delete this menu item?')) {
            return;
        }
        if (currentEditingMenu) {
            currentEditingMenu.menu_data = currentEditingMenu.menu_data.filter(item => item.id !== itemId);
            renderMenuItems(currentEditingMenu.menu_data);
        }
    }

    /**
     * Saves the reordered/updated menu items to the backend.
     */
    saveMenuItemsOrderButton.addEventListener('click', async () => {
        if (!currentEditingMenu) return;

        const newOrder = [];
        $(menuItemsSortable).children('li').each(function() {
            const itemId = $(this).data('id');
            const originalItem = currentEditingMenu.menu_data.find(item => item.id === itemId);
            if (originalItem) {
                newOrder.push(originalItem);
            }
        });
        currentEditingMenu.menu_data = newOrder; // Update the in-memory menu_data

        try {
            const response = await fetch(`/api/admin/menus/${currentEditingMenu.name}`, {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify({ menu_data: currentEditingMenu.menu_data })
            });

            const data = await response.json();

            if (response.ok) {
                alert('Menu structure saved successfully!');
                loadMenuBuilder(); // Reload menu list
            } else {
                alert(data.message || 'Failed to save menu structure.');
            }
        } catch (error) {
            console.error('Error saving menu structure:', error);
            alert('An error occurred while saving the menu structure.');
        }
    });

    /**
     * Cancels menu editing and returns to the menu list.
     */
    cancelMenuEditButton.addEventListener('click', () => {
        currentEditingMenu = null;
        menuEditorArea.style.display = 'none';
        menusList.style.display = 'block';
        loadMenuBuilder();
    });

    /**
     * Deletes an entire menu.
     * @param {string} menuName - The name of the menu to delete.
     */
    async function deleteMenu(menuName) {
        if (!confirm(`Are you sure you want to delete the menu "${menuName}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/menus/${menuName}`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });

            const data = await response.json();

            if (response.ok) {
                alert('Menu deleted successfully!');
                loadMenuBuilder();
            } else {
                alert(data.message || 'Failed to delete menu.');
            }
        } catch (error) {
            console.error('Error deleting menu:', error);
            alert('An error occurred while deleting the menu.');
        }
    });

    // Event listener for "Add Menu Item" button
    addMenuItemButton.addEventListener('click', () => openMenuItemModal());

    // --- Widget System Management ---

    /**
     * Loads all widgets and renders them in the dashboard.
     */
    async function loadWidgetSystem() {
        try {
            const response = await fetch('/api/admin/widgets', { headers: getAuthHeaders() });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const widgets = await response.json();
            renderWidgetsList(widgets);
        } catch (error) {
            console.error('Error fetching widgets:', error);
            widgetsList.innerHTML = '<p class="text-danger">Failed to load widgets.</p>';
            if (error.message.includes('401')) {
                alert('Session expired. Please log in again.'); // Use alert for now
                logoutButton.click();
            }
        }
    }

    /**
     * Renders the list of all widgets in the dashboard.
     * @param {Array} widgets - The array of widget objects.
     */
    function renderWidgetsList(widgets) {
        widgetsList.innerHTML = '';
        if (widgets.length === 0) {
            widgetsList.innerHTML = '<p>No widgets found. Add a new widget.</p>';
            return;
        }

        const ul = document.createElement('ul');
        ul.classList.add('list-group');

        widgets.forEach(widget => {
            const li = document.createElement('li');
            li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
            li.innerHTML = `
                <span>${widget.name} (${widget.widget_type})</span>
                <div>
                    <button class="btn btn-sm btn-info edit-widget-btn me-2" data-name="${widget.name}">Edit</button>
                    <button class="btn btn-sm btn-danger delete-widget-btn" data-name="${widget.name}">Delete</button>
                </div>
            `;
            ul.appendChild(li);
        });
        widgetsList.appendChild(ul);

        document.querySelectorAll('.edit-widget-btn').forEach(button => {
            button.addEventListener('click', (e) => openEditWidgetModal(e.target.dataset.name));
        });
        document.querySelectorAll('.delete-widget-btn').forEach(button => {
            button.addEventListener('click', (e) => deleteWidget(e.target.dataset.name));
        });
    }

    /**
     * Dynamically renders input fields for widget data based on widget type.
     * @param {string} widgetType - The type of widget.
     * @param {HTMLElement} container - The DOM element to render fields into.
     * @param {Object} [data={}] - Existing widget data to pre-populate fields.
     */
    function renderWidgetDataFields(widgetType, container, data = {}) {
        container.innerHTML = ''; // Clear existing fields
        let fieldsHtml = '';

        switch (widgetType) {
            case 'text':
                fieldsHtml = `
                    <label for="widget-text-content" class="form-label">Content (HTML/Text)</label>
                    <textarea class="form-control" id="widget-text-content" rows="5">${data.content || ''}</textarea>
                `;
                break;
            case 'image':
                fieldsHtml = `
                    <label for="widget-image-url" class="form-label">Image URL</label>
                    <input type="text" class="form-control mb-2" id="widget-image-url" value="${data.url || ''}">
                    <label for="widget-image-alt" class="form-label">Alt Text</label>
                    <input type="text" class="form-control" id="widget-image-alt" value="${data.alt || ''}">
                `;
                break;
            case 'social':
                fieldsHtml = `
                    <label for="widget-social-facebook" class="form-label">Facebook URL</label>
                    <input type="url" class="form-control mb-2" id="widget-social-facebook" value="${data.facebook || ''}">
                    <label for="widget-social-twitter" class="form-label">Twitter URL</label>
                    <input type="url" class="form-control mb-2" id="widget-social-twitter" value="${data.twitter || ''}">
                    <label for="widget-social-instagram" class="form-label">Instagram URL</label>
                    <input type="url" class="form-control" id="widget-social-instagram" value="${data.instagram || ''}">
                `;
                break;
            // Add cases for other widget types
            default:
                fieldsHtml = '<p class="text-muted">No specific fields for this widget type.</p>';
                break;
        }
        container.innerHTML = fieldsHtml;
        container.style.display = 'block';
    }

    /**
     * Extracts widget data from the form based on widget type.
     * @param {string} widgetType - The type of widget.
     * @param {string} prefix - Prefix for input IDs (e.g., 'new-widget-' or 'edit-widget-').
     * @returns {Object} The extracted widget data.
     */
    function getWidgetDataFromForm(widgetType, prefix) {
        const data = {};
        switch (widgetType) {
            case 'text':
                data.content = document.getElementById(`${prefix}text-content`).value;
                break;
            case 'image':
                data.url = document.getElementById(`${prefix}image-url`).value;
                data.alt = document.getElementById(`${prefix}image-alt`).value;
                break;
            case 'social':
                data.facebook = document.getElementById(`${prefix}social-facebook`).value;
                data.twitter = document.getElementById(`${prefix}social-twitter`).value;
                data.instagram = document.getElementById(`${prefix}social-instagram`).value;
                break;
        }
        return data;
    }

    // Event listener for new widget type selection
    newWidgetTypeSelect.addEventListener('change', (e) => {
        renderWidgetDataFields(e.target.value, newWidgetDataContainer);
    });

    // Event listener for add widget form submission
    addWidgetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('new-widget-name').value;
        const type = newWidgetTypeSelect.value;
        const widgetData = getWidgetDataFromForm(type, 'widget-');

        if (!name || !type) {
            alert('Widget name and type are required.'); // Use alert for now
            return;
        }

        try {
            const response = await fetch('/api/admin/widgets', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ name, widget_type: type, widget_data: widgetData })
            });

            const data = await response.json();

            if (response.ok) {
                alert('Widget created successfully!'); // Use alert for now
                $('#addWidgetModal').modal('hide');
                addWidgetForm.reset();
                newWidgetDataContainer.innerHTML = ''; // Clear dynamic fields
                newWidgetDataContainer.style.display = 'none';
                loadWidgetSystem();
            } else {
                alert(data.message || 'Failed to create widget.'); // Use alert for now
            }
        } catch (error) {
            console.error('Error adding widget:', error);
            alert('An error occurred while creating the widget.'); // Use alert for now
        }
    });

    /**
     * Opens the edit widget modal and populates it with existing widget data.
     * @param {string} widgetName - The name of the widget to edit.
     */
    async function openEditWidgetModal(widgetName) {
        try {
            const response = await fetch(`/api/admin/widgets/${widgetName}`, { headers: getAuthHeaders() });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            currentEditingWidget = await response.json();

            editWidgetNameHidden.value = currentEditingWidget.name;
            editWidgetNameInput.value = currentEditingWidget.name;
            editWidgetTypeSelect.value = currentEditingWidget.widget_type;

            renderWidgetDataFields(currentEditingWidget.widget_type, editWidgetDataContainer, currentEditingWidget.widget_data);

            $('#editWidgetModal').modal('show');
        } catch (error) {
            console.error('Error opening edit widget modal:', error);
            alert('Failed to load widget data for editing.');
        }
    }

    // Event listener for edit widget type selection
    editWidgetTypeSelect.addEventListener('change', (e) => {
        renderWidgetDataFields(e.target.value, editWidgetDataContainer, currentEditingWidget.widget_data);
    });

    // Event listener for edit widget form submission
    editWidgetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = editWidgetNameHidden.value;
        const type = editWidgetTypeSelect.value;
        const widgetData = getWidgetDataFromForm(type, 'edit-widget-');

        if (!name || !type) {
            alert('Widget name and type are required.');
            return;
        }

        try {
            const response = await fetch(`/api/admin/widgets/${name}`, {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify({ widget_type: type, widget_data: widgetData })
            });

            const data = await response.json();

            if (response.ok) {
                alert('Widget updated successfully!');
                $('#editWidgetModal').modal('hide');
                loadWidgetSystem();
            } else {
                alert(data.message || 'Failed to update widget.');
            }
        } catch (error) {
            console.error('Error updating widget:', error);
            alert('An error occurred while updating the widget.');
        }
    });

    // Event listener for delete widget button
    deleteWidgetButton.addEventListener('click', async () => {
        if (!currentEditingWidget) return;

        if (!confirm(`Are you sure you want to delete the widget "${currentEditingWidget.name}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/admin/widgets/${currentEditingWidget.name}`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });

            const data = await response.json();

            if (response.ok) {
                alert('Widget deleted successfully!');
                $('#editWidgetModal').modal('hide');
                loadWidgetSystem();
            } else {
                alert(data.message || 'Failed to delete widget.');
            }
        } catch (error) {
            console.error('Error deleting widget:', error);
            alert('An error occurred while deleting the widget.');
        }
    });

    // --- Event Listeners for Tabs ---
    document.getElementById('pages-tab').addEventListener('shown.bs.tab', loadAdminData);
    document.getElementById('menus-tab').addEventListener('shown.bs.tab', loadMenuBuilder);
    document.getElementById('widgets-tab').addEventListener('shown.bs.tab', loadWidgetSystem);
    document.getElementById('settings-tab').addEventListener('shown.bs.tab', fetchCMSSettings);


    // --- Image Upload ---

    /**
     * Handles image file uploads.
     * @param {Event} e - The form submission event.
     */
    imageUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const fileInput = document.getElementById('image-file');
        if (fileInput.files.length === 0) {
            alert('Please select a file to upload.'); // Use alert for now
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('/api/admin/upload', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${adminToken}` }, // No 'Content-Type' for FormData
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                alert(`Image uploaded successfully! URL: ${data.file_path}`); // Use alert for now
                fileInput.value = ''; // Clear file input
                // Optionally, update an image field in an open modal
                // e.g., document.getElementById('edit-page-image').value = data.file_path;
            } else {
                alert(data.message || 'Image upload failed.'); // Use alert for now
            }
        } catch (error) {
            console.error('Error uploading image:', error);
            alert('An error occurred during image upload.'); // Use alert for now
        }
    });

    // --- Initial Load ---
    if (isAuthenticated()) {
        showAdminDashboard();
    } else {
        // If not authenticated, redirect to login page
        window.location.href = '/admin.html';
    }
});
