// public/js/employee_login.js
// Simple employee login by Somabay domain email. Sets a session on the backend.

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('employee-login-form');
  const messageEl = document.getElementById('employee-login-message');

  function showMessage(msg, isError = false) {
    messageEl.textContent = msg;
    messageEl.className = `mt-3 text-${isError ? 'danger' : 'success'}`;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('employee-email').value.trim();

    // Client-side validation: must contain "@somabay"
    if (!/@somabay/i.test(email)) {
      showMessage('Please use your Somabay email address (must contain @somabay).', true);
      return;
    }

    try {
      const res = await fetch('/api/employee/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        showMessage('Login successful. Redirecting...');
        // Redirect to home to see private pages in sidebar
        setTimeout(() => (window.location.href = '/'), 500);
      } else {
        showMessage(data.message || 'Login failed. Please use a Somabay email.', true);
      }
    } catch (err) {
      console.error('Employee login error:', err);
      showMessage('Error during login. Please try again.', true);
    }
  });
});