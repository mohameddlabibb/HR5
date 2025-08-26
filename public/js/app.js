// public/js/app.js
// Client-side JavaScript for the Somabay Handbook website.
// Handles dynamic loading of sidebar navigation and page content.

document.addEventListener('DOMContentLoaded', () => {
    const sidebarMenu = document.getElementById('sidebar-menu');
    const pageTitleElement = document.getElementById('page-title');
    const headerImageElement = document.getElementById('header-image');
    const pageContentElement = document.getElementById('page-content');
    const contentHeaderElement = document.getElementById('content-header');
    const metaDescriptionElement = document.querySelector('meta[name="description"]');
    const metaKeywordsElement = document.querySelector('meta[name="keywords"]');

    let sidebarData = []; // Stores the full sidebar structure

// Adjust this if your backend runs somewhere else
const API_BASE_URL = "http://localhost:5000";

/**
 * Fetches the sidebar data from the backend API.
 * @returns {Promise<Array>} A promise that resolves with the sidebar data.
 */
async function fetchSidebar() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/sidebar`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        sidebarData = await response.json();
        renderSidebar(sidebarData, sidebarMenu);
        handleInitialPageLoad();
    } catch (error) {
        console.error('Error fetching sidebar:', error);
        sidebarMenu.innerHTML = '<p class="text-danger p-3">Failed to load navigation.</p>';
    }
}

    /**
     * Renders the sidebar menu recursively.
     * @param {Array} items - The array of sidebar items (pages or chapters).
     * @param {HTMLElement} parentElement - The DOM element to append the menu to.
     */
    function renderSidebar(items, parentElement) {
        parentElement.innerHTML = ''; // Clear existing menu
        items.forEach(item => {
            const menuItem = document.createElement('div');
            menuItem.classList.add('menu-item');

            const menuLink = document.createElement('a');
            menuLink.href = item.slug ? `/pages/${item.slug}` : '#'; // Use slug for page links
            menuLink.classList.add('menu-link');
            menuLink.textContent = item.title;
            menuLink.dataset.slug = item.slug; // Store slug for easy access

            // Handle chapter (has children)
            if (item.children && item.children.length > 0) {
                menuItem.classList.add('has-children');
                menuLink.addEventListener('click', (e) => {
                    e.preventDefault(); // Prevent default link behavior for chapters
                    menuItem.classList.toggle('expanded');
                    const submenu = menuItem.querySelector('.submenu');
                    if (submenu) {
                        submenu.style.display = menuItem.classList.contains('expanded') ? 'block' : 'none';
                    }
                });
            } else if (item.slug) {
                // Handle actual page links
                menuLink.addEventListener('click', (e) => {
                    e.preventDefault(); // Prevent full page reload
                    navigateToPage(item.slug);
                });
            }

            menuItem.appendChild(menuLink);

            if (item.children && item.children.length > 0) {
                const submenu = document.createElement('ul');
                submenu.classList.add('submenu');
                renderSidebar(item.children, submenu); // Recursively render children
                menuItem.appendChild(submenu);
            }

            parentElement.appendChild(menuItem);
        });
    }

    /**
     * Handles initial page load based on the URL hash or path.
     */
    function handleInitialPageLoad() {
        const path = window.location.pathname;
        const slugMatch = path.match(/\/pages\/(.*)/);
        if (slugMatch && slugMatch[1]) {
            navigateToPage(slugMatch[1], false); // Load page without pushing to history again
        } else {
            // Optionally load a default homepage if no slug is present
            // For now, the index.html already has placeholder content.
            // We could fetch a specific 'home' page if it existed in pages.json
        }
    }

    /**
     * Navigates to a specific page by slug, updates URL, and loads content.
     * @param {string} slug - The slug of the page to navigate to.
     * @param {boolean} pushState - Whether to push a new state to browser history (default: true).
     */
    async function navigateToPage(slug, pushState = true) {
        try {
            // Fetch page content from backend
            const response = await fetch(`/api/pages/${slug}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const page = await response.json();

            // Update URL
            if (pushState) {
                window.history.pushState({ slug: page.slug }, page.title, `/pages/${page.slug}`);
            }

            // Update page title and content
            pageTitleElement.textContent = page.title;
            pageContentElement.innerHTML = page.content;

            // Update meta tags
            if (metaDescriptionElement) {
                metaDescriptionElement.setAttribute('content', page.meta_description || '');
            }
            if (metaKeywordsElement) {
                metaKeywordsElement.setAttribute('content', page.meta_keywords || '');
            }

            // Update header image and color
            if (page.design) {
                contentHeaderElement.style.setProperty('--header-color', page.design.headerColor || '#f8f9fa');
                if (page.design.headerImage) {
                    headerImageElement.src = page.design.headerImage;
                    headerImageElement.style.display = 'block';
                } else {
                    headerImageElement.style.display = 'none';
                }
            } else {
                contentHeaderElement.style.setProperty('--header-color', '#f8f9fa');
                headerImageElement.style.display = 'none';
            }

            highlightActiveLink(slug); // Highlight active link in sidebar
        } catch (error) {
            console.error('Error loading page content:', error);
            pageTitleElement.textContent = 'Page Not Found';
            pageContentElement.innerHTML = '<p class="text-danger">The requested page could not be loaded.</p>';
            headerImageElement.style.display = 'none';
            contentHeaderElement.style.setProperty('--header-color', '#f8f9fa');
            if (metaDescriptionElement) metaDescriptionElement.setAttribute('content', '');
            if (metaKeywordsElement) metaKeywordsElement.setAttribute('content', '');
        }
    }

    /**
     * Highlights the active link in the sidebar menu.
     * @param {string} activeSlug - The slug of the currently active page.
     */
    function highlightActiveLink(activeSlug) {
        // Remove active class from all links
        document.querySelectorAll('.sidebar-menu .menu-link, .sidebar-menu .submenu-link').forEach(link => {
            link.classList.remove('active');
            // Also collapse all submenus first
            const parentMenuItem = link.closest('.menu-item.has-children');
            if (parentMenuItem) {
                parentMenuItem.classList.remove('expanded');
                const submenu = parentMenuItem.querySelector('.submenu');
                if (submenu) submenu.style.display = 'none';
            }
        });

        // Find and add active class to the current page's link
        const currentLink = document.querySelector(`.sidebar-menu a[data-slug="${activeSlug}"]`);
        if (currentLink) {
            currentLink.classList.add('active');

            // Expand parent menus if necessary
            let parent = currentLink.closest('.submenu');
            while (parent) {
                const parentMenuItem = parent.closest('.menu-item.has-children');
                if (parentMenuItem) {
                    parentMenuItem.classList.add('expanded');
                    parent.style.display = 'block';
                    parent = parentMenuItem.closest('.submenu'); // Continue up the hierarchy
                } else {
                    parent = null;
                }
            }
        }
    }

    // Handle browser's back/forward buttons
    window.addEventListener('popstate', (event) => {
        const path = window.location.pathname;
        const slugMatch = path.match(/\/pages\/(.*)/);
        if (slugMatch && slugMatch[1]) {
            navigateToPage(slugMatch[1], false); // Load page without pushing to history again
        } else {
            // If navigating back to root, reset content or load default
            pageTitleElement.textContent = 'Welcome to Somabay Handbook';
            pageContentElement.innerHTML = `
                <p>Select an item from the sidebar to view its content.</p>
                <p>This is a placeholder for the main content area. The actual content will be loaded dynamically based on your selection in the sidebar navigation.</p>
                <p>Here's a placeholder image:</p>
                <img src="/uploads/placeholder-image.jpg" alt="Placeholder Content Image" class="img-fluid content-image">
                <p>And a placeholder video:</p>
                <div class="video-container">
                    <iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                </div>
            `;
            headerImageElement.src = "/uploads/default-header.jpg";
            headerImageElement.style.display = 'block';
            contentHeaderElement.style.setProperty('--header-color', '#f8f9fa');
            highlightActiveLink(null); // Clear active highlight
        }
    });

    // Initial fetch and render
    fetchSidebar();
});
