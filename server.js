// server.js
const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = 3000;

// ✅ Proxy all /api requests to Flask backend on port 5000
// app.use(
//   '/api',
//   createProxyMiddleware({
//     target: 'http://127.0.0.1:5000',
//     changeOrigin: true,
//   })
// );

// ✅ Serve static frontend files
app.use(express.static(path.join(__dirname, 'public')));

// Serve admin.html
app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'admin.html'));
});

app.get('/admin_panel', (req, res) => {
    res.setHeader('Content-Type', 'text/html');
    res.sendFile(path.join(__dirname, 'public', 'admin_panel.html'));
  });

// ✅ Handle React/HTML fallback (if frontend routing is used)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
