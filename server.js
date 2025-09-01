// server.js
const express = require('express');
const path = require('path');
const mime = require('mime-types'); // Import mime-types
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = 3000;

// Serve admin pages directly from Node static files
app.get('/admin_panel', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'admin_panel.html'));
});
app.get('/admin.html', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'admin.html'));
});

// ✅ Serve static frontend files under /public to match Flask paths
app.use('/public', express.static(path.join(__dirname, 'public'), {
  setHeaders: (res, filePath) => {
    if (mime.lookup(filePath) === 'application/javascript') {
      res.setHeader('Content-Type', 'application/javascript');
    }
  }
}));



// ✅ Handle React/HTML fallback (if frontend routing is used)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
