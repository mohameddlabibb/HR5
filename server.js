// server.js
// Node.js static file server for the Somabay Handbook website.
// This server handles serving static frontend files and routes for the main application and admin panel.

const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files from the 'public' directory
// This middleware makes all files in the 'public' folder accessible directly via their URL.
// For example, 'public/index.html' can be accessed at '/index.html'.
app.use(express.static(path.join(__dirname, 'public')));

// Serve uploaded images from the 'public/uploads' directory
// This allows images uploaded via the admin panel to be served publicly.
app.use('/uploads', express.static(path.join(__dirname, 'public', 'uploads')));

// Serve data files from the 'data' directory
app.use('/data', express.static(path.join(__dirname, 'data')));

// Route for the admin panel
// When a request comes to '/admin', serve the 'admin.html' file.
app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'admin.html'));
});

// Catch-all route for client-side routing
// For any other GET request, serve the 'index.html' file.
// This is crucial for single-page applications (SPAs) where client-side JavaScript
// handles routing for different pages (e.g., /pages/our-company-shareholders).
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
    console.log(`Frontend static server running on http://localhost:${PORT}`);
    console.log(`Admin panel accessible at http://localhost:${PORT}/admin`);
});
