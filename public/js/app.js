// public/js/app.js
// Client-side JavaScript for the Somabay Handbook website.
// Handles dynamic loading of sidebar navigation and page content.

document.addEventListener('DOMContentLoaded', () => {
    const sidebarMenu = document.getElementById('sidebar-menu');
    const pageTitleElement = document.getElementById('page-title');
    const pageContentElement = document.getElementById('page-content');
    const breadcrumbsElement = document.getElementById('breadcrumbs');

    // Function to fetch pages data from backend via same-origin proxy to avoid CORS issues
    async function fetchPagesData() {
        try {
            // Use relative URL so it works behind the Node proxy (/api -> Flask)
            const response = await fetch('/api/sidebar');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Fetched pages data:', data); // Log fetched data
            return data;
        } catch (error) {
            console.error('Error fetching pages data:', error);
            // Show friendly message when backend is down or unreachable via proxy
            const container = document.getElementById('page-content');
            if (container) {
                container.innerHTML = '<div class="alert alert-warning">Backend API is not reachable. Make sure Flask is running on port 5000. The Node server on port 3000 proxies /api to http://localhost:5000.</div>';
            }
            return [];
        }
    }

    // Function to build sidebar menu
    function buildSidebarMenu(pages, parentElement) {
        console.log('Building sidebar with pages:', pages);
        pages.forEach(page => {
            if (!page.published) return;

            const menuItem = document.createElement('div');
            menuItem.classList.add('menu-item');

            const menuLink = document.createElement('a');
            menuLink.classList.add('menu-link');
            menuLink.textContent = page.title;

            if (page.slug) {
                menuLink.href = `/pages/${page.slug}`;
            } else {
                menuLink.href = '#';
                menuItem.classList.add('has-children');
                menuLink.setAttribute('aria-expanded', 'false');
            }

            menuItem.appendChild(menuLink);

            if (page.children && page.children.length > 0) {
                console.log(`Page "${page.title}" has children:`, page.children);

                const submenu = document.createElement('div'); // changed from ul to div for flexibility
                submenu.classList.add('submenu');
                submenu.style.display = 'none'; // collapse by default

                buildSidebarMenu(page.children, submenu);
                menuItem.appendChild(submenu);

                // Add click event to toggle submenu
                menuLink.addEventListener('click', (e) => {
                    if (menuLink.getAttribute('href') === '#') {
                        e.preventDefault();
                        const isExpanded = menuItem.classList.contains('expanded');

                        if (isExpanded) {
                            submenu.style.display = 'none';
                            menuItem.classList.remove('expanded');
                            menuLink.setAttribute('aria-expanded', 'false');
                        } else {
                            submenu.style.display = 'block';
                            menuItem.classList.add('expanded');
                            menuLink.setAttribute('aria-expanded', 'true');
                        }
                    }
                });
            }

            parentElement.appendChild(menuItem);
        });
    }

    // Highlights the active link based on current URL
    function highlightActiveLink() {
        const currentPath = window.location.pathname;
        console.log('highlightActiveLink called with currentPath:', currentPath);

        document.querySelectorAll('.sidebar-menu .menu-link, .sidebar-menu .submenu-link').forEach(link => {
            link.classList.remove('active');
            const parentMenuItem = link.closest('.menu-item.has-children');
            if (parentMenuItem) {
                parentMenuItem.classList.remove('expanded');
            }
        });

        let activeLink = null;
        if (currentPath === '/index.html' || currentPath === '/') {
            activeLink = document.querySelector('.sidebar-menu a[href="/index.html"]');
        } else {
            activeLink = document.querySelector(`.sidebar-menu a[href="${currentPath}"]`);
        }

        if (activeLink) {
            activeLink.classList.add('active');

            let parent = activeLink.closest('.submenu');
            while (parent) {
                const parentMenuItem = parent.closest('.menu-item.has-children');
                if (parentMenuItem) {
                    parentMenuItem.classList.add('expanded');
                    parent.style.display = 'block';
                    parentMenuItem.querySelector('.menu-link').setAttribute('aria-expanded', 'true');
                    parent = parentMenuItem.closest('.submenu');
                } else {
                    parent = null;
                }
            }
        }
    }

    async function loadPageContent(pageSlugParam = null) {
        let actualPageSlug = pageSlugParam;

        try {
            // If pageSlugParam is not provided, determine slug from URL
            if (!actualPageSlug) {
                const path = window.location.pathname;
                actualPageSlug = path.replace(/^\/pages\//, '').replace(/\.html$/, '');
            } else {
                actualPageSlug = actualPageSlug.replace(/^\/pages\//, '').replace(/\.html$/, '');
            }

            // Clean up leading slashes and handle root/index cases
            actualPageSlug = actualPageSlug.replace(/^\/+/, '');
            
            if (!actualPageSlug || actualPageSlug === 'index') {
                // Avoid calling /api/pages/index; nothing to show yet
                return;
            }

            // Fetch page data from backend via same-origin proxy
            const response = await fetch(`/api/pages/${actualPageSlug}`);
            if (response.status === 401) {
                // Require employee login for private content
                window.location.href = '/public/employee_login.html';
                return;
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const pageData = await response.json();
            console.log('Page data:', pageData);

            // Update page title and content
            if (pageTitleElement) pageTitleElement.textContent = pageData.title || 'Page Not Found';
            if (pageContentElement) pageContentElement.innerHTML = pageData.content || '<p>Content not found.</p>';

            // Media placeholders removed; CKEditor content will handle embedded media within page content.

            // Update breadcrumbs (render exactly what the backend sends to avoid duplicates)
            if (breadcrumbsElement && pageData.breadcrumbs) {
                let html = '<ol class="breadcrumb">';
                pageData.breadcrumbs.forEach(crumb => {
                    if (crumb.active) {
                        html += `<li class="breadcrumb-item active" aria-current="page">${crumb.title}</li>`;
                    } else {
                        html += `<li class="breadcrumb-item"><a href="${crumb.url}">${crumb.title}</a></li>`;
                    }
                });
                html += '</ol>';
                breadcrumbsElement.innerHTML = html;
            }

            // Don't replace the sidebar - it's already built correctly with proper hierarchy
            // The pageData.sidebar is sent by the backend but we don't need to re-render it
            // since the initial sidebar build already handles the hierarchical structure properly

        } catch (error) {
            console.error('Error loading page content:', error);
            if (pageTitleElement) pageTitleElement.textContent = 'Error';
            if (pageContentElement) pageContentElement.innerHTML = '<p>Failed to load content.</p>';
        }
    }

    // Initialize sidebar and content
    fetchPagesData().then(pagesData => {
        buildSidebarMenu(pagesData, sidebarMenu);

        // Collapse all submenus after building the menu
        document.querySelectorAll('.sidebar-menu .menu-item.has-children').forEach(item => {
            item.classList.remove('expanded');
            item.querySelector('.menu-link').setAttribute('aria-expanded', 'false');
            const submenu = item.querySelector('.submenu');
            if (submenu) submenu.style.display = 'none';
        });

        // Initial load: if landing on / or /index.html, try loading default page if any
        highlightActiveLink();
        const initialPath = window.location.pathname === '/' ? '/index.html' : window.location.pathname;
        loadPageContent(initialPath);

        sidebarMenu.addEventListener('click', (e) => {
            const link = e.target.closest('.menu-link, .submenu-link');
            if (link && link.href && link.getAttribute('href') !== '#') {
                e.preventDefault();
                const pagePath = link.getAttribute('href');
                history.pushState(null, '', pagePath);
                loadPageContent(pagePath);
                highlightActiveLink();
            }
        });

        window.addEventListener('popstate', () => {
            highlightActiveLink();
            const popStatePath = window.location.pathname === '/' ? '/index.html' : window.location.pathname;
            loadPageContent(popStatePath);
        });
    });
});
