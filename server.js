// server.js
const express = require('express');
const path = require('path');
const mime = require('mime-types'); // Import mime-types
const http = require('http');

const app = express();
const PORT = 3000;

// ✅ Manual proxy for API requests to Flask backend
app.use('/api/*', (req, res) => {
  console.log('Proxying request:', req.method, req.originalUrl);
  
  const options = {
    hostname: 'localhost',
    port: 5000,
    path: req.originalUrl,
    method: req.method,
    headers: {
      ...req.headers,
      host: 'localhost:5000'
    }
  };

  const proxyReq = http.request(options, (proxyRes) => {
    console.log('Proxy response:', proxyRes.statusCode, 'for', req.originalUrl);
    
    // Set response headers
    res.status(proxyRes.statusCode);
    Object.keys(proxyRes.headers).forEach(key => {
      res.set(key, proxyRes.headers[key]);
    });

    // Pipe the response
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('Proxy error:', err.message);
    res.status(500).json({ error: 'Backend service unavailable' });
  });

  // Pipe the request body if it exists
  req.pipe(proxyReq);
});

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

// ✅ Serve uploaded assets at /uploads from public/uploads (images/videos)
app.use('/uploads', express.static(path.join(__dirname, 'public', 'uploads')));

// ✅ Handle React/HTML fallback (if frontend routing is used)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
