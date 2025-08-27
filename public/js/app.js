// public/js/app.js
// Client-side JavaScript for the Somabay Handbook website.
// Handles dynamic loading of sidebar navigation and page content.

document.addEventListener('DOMContentLoaded', () => {
    const sidebarMenu = document.getElementById('sidebar-menu');
    const pageTitleElement = document.getElementById('page-title');
    const pageContentElement = document.getElementById('page-content');
    const breadcrumbsElement = document.getElementById('breadcrumbs');

    // Function to fetch JSON data
    async function fetchPagesData() {
        try {
            const response = await fetch('data/pages.json'); // Relative path
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Fetched pages data:', data); // Log fetched data
            return data;
        } catch (error) {
            console.error('Error fetching pages data:', error);
            return [];
        }
    }

    // Function to build sidebar menu
    function buildSidebarMenu(pages, parentElement) {
        console.log('Building sidebar with pages:', pages); // Log pages being used to build sidebar
        pages.forEach(page => {
            if (!page.published) return;

            const menuItem = document.createElement('div');
            menuItem.classList.add('menu-item');

            const menuLink = document.createElement('a');
            menuLink.classList.add('menu-link');
            menuLink.textContent = page.title;

            if (page.slug) {
                menuLink.href = `/pages/${page.slug}.html`; // Absolute path from server root
            } else {
                menuLink.href = '#'; // Parent items without a specific page
                menuItem.classList.add('has-children');
                menuLink.setAttribute('aria-expanded', 'false');
            }

            menuItem.appendChild(menuLink);

            if (page.children && page.children.length > 0) {
                console.log(`Page "${page.title}" has children:`, page.children); // Log children
                const submenu = document.createElement('ul');
                submenu.classList.add('submenu');
                buildSidebarMenu(page.children, submenu);
                menuItem.appendChild(submenu);

                menuLink.addEventListener('click', (e) => {
                    console.log('Click event triggered on:', e.target); // Log the clicked element
                    if (menuLink.getAttribute('href') === '#') {
                        e.preventDefault();
                        console.log('Before toggle - expanded:', menuItem.classList.contains('expanded')); // Log before toggle
                        menuItem.classList.toggle('expanded');
                        console.log('After toggle - expanded:', menuItem.classList.contains('expanded')); // Log after toggle
                        menuLink.setAttribute('aria-expanded', menuItem.classList.contains('expanded') ? 'true' : 'false');
                    }
                });
            }
            parentElement.appendChild(menuItem);
        });
    }

    /**
     * Highlights the active link in the sidebar menu based on the current URL.
     */
    function highlightActiveLink() {
        const currentPath = window.location.pathname;

        // Remove active class from all links
        document.querySelectorAll('.sidebar-menu .menu-link, .sidebar-menu .submenu-link').forEach(link => {
            link.classList.remove('active');
            // Collapse all submenus first by removing the 'expanded' class
            const parentMenuItem = link.closest('.menu-item.has-children');
            if (parentMenuItem) {
                parentMenuItem.classList.remove('expanded');
            }
        });

        // Find and add active class to the current page's link
        // Adjust for '/pages/slug.html' or '/index.html'
        let activeLink = null;
        if (currentPath === '/index.html' || currentPath === '/') {
            activeLink = document.querySelector('.sidebar-menu a[href="/index.html"]'); // Absolute path
        } else {
            // For static pages, the href will be /pages/slug.html
            activeLink = document.querySelector(`.sidebar-menu a[href="${currentPath}"]`); // Absolute path
        }
        
        if (activeLink) {
            activeLink.classList.add('active');

            // Expand parent menus if necessary
            let parent = activeLink.closest('.submenu');
            while (parent) {
                const parentMenuItem = parent.closest('.menu-item.has-children');
                if (parentMenuItem) {
                    parentMenuItem.classList.add('expanded');
                    parent = parentMenuItem.closest('.submenu'); // Continue up the hierarchy
                } else {
                    parent = null;
                }
            }
        }
    }

    // Function to load page content dynamically
    async function loadPageContent(pagePath) {
        try {
            const response = await fetch(pagePath);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const contentSection = doc.querySelector('.content-section');
            const pageTitle = doc.querySelector('h1'); 
            const breadcrumbContent = doc.querySelector('.breadcrumb');

            if (pageTitleElement) {
                pageTitleElement.textContent = pageTitle ? pageTitle.textContent : 'Page Not Found';
            }
            if (pageContentElement) {
                pageContentElement.innerHTML = contentSection ? contentSection.innerHTML : '<p>Content not found.</p>';
            }
            if (breadcrumbsElement) {
                breadcrumbsElement.innerHTML = breadcrumbContent ? breadcrumbContent.innerHTML : '';
            }

        } catch (error) {
            console.error('Error loading page content:', error);
            if (pageTitleElement) pageTitleElement.textContent = 'Error';
            if (pageContentElement) pageContentElement.innerHTML = '<p>Failed to load content.</p>';
        }
    }

    // Load sidebar and then highlight
    fetchPagesData().then(pagesData => {
        buildSidebarMenu(pagesData, sidebarMenu);
        highlightActiveLink();
        
        // Add event listeners for sidebar links to load content
        sidebarMenu.addEventListener('click', (e) => {
            const link = e.target.closest('.menu-link, .submenu-link');
            if (link && link.href && link.getAttribute('href') !== '#') {
                e.preventDefault();
                const pagePath = link.getAttribute('href');
                history.pushState(null, '', pagePath); // Update URL without full reload
                loadPageContent(pagePath);
                highlightActiveLink();
            }
        });

        // Re-highlight and load content on browser history navigation (back/forward)
        window.addEventListener('popstate', () => {
            highlightActiveLink();
            const popStatePath = window.location.pathname === '/' ? '/index.html' : window.location.pathname;
            loadPageContent(popStatePath);
        });
    });
});
