// public/js/admin.js
// Client-side JavaScript for the Somabay Handbook Admin Login.

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const loginMessage = document.getElementById('login-message');

    let adminToken = localStorage.getItem('adminToken'); // Retrieve token from local storage

    /**
     * Displays a message to the user.
     * @param {HTMLElement} element - The DOM element to display the message in.
     * @param {string} message - The message text.
     * @param {boolean} isError - True if it's an error message, false otherwise.
     */
    function showMessage(element, message, isError = false) {
        element.textContent = message;
        element.className = `mt-3 text-${isError ? 'danger' : 'success'}`;
    }

    /**
     * Handles the admin login process.
     * @param {Event} e - The form submission event.
     */
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        console.log('Attempting login with username:', username); // Debugging

        try {
            const response = await fetch('http://localhost:5000/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();
            console.log('Login API response:', data); // Debugging

            if (response.ok) {
                adminToken = data.access_token;
                localStorage.setItem('adminToken', adminToken); // Store token
                showMessage(loginMessage, 'Login successful!', false);
                window.location.href = '/admin_panel';  // redirect
            } else {
                console.log('Login failed:', data.message); // Debugging
                showMessage(loginMessage, data.message || 'Login failed.', true);
            }
        } catch (error) {
            console.error('Login error:', error);
            showMessage(loginMessage, 'An error occurred during login. Check console for details.', true);
        }
    });

    // Check if already authenticated on page load (e.g., if user navigates back)
    if (adminToken) {
        // Optionally, validate token with a quick API call
        // For now, just redirect if token exists
        window.location.href = '/admin_panel';
    }
});
