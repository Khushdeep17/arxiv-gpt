const express = require('express');
const axios = require('axios');
const path = require('path');
const cors = require('cors');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

// Middleware
app.use(cors());
app.use(express.json());

// Serve React frontend if exists
const frontendPath = path.join(__dirname, '../frontend/build');
if (fs.existsSync(frontendPath)) {
  app.use(express.static(frontendPath));
}

// Helper function to sanitize filenames
function sanitizeFilename(filename) {
  return path.basename(filename.replace(/\\/g, '/').trim());
}

// Proxy /api requests to FastAPI backend
app.use('/api', async (req, res) => {
  try {
    const url = `${BACKEND_URL}${req.path}${req.url.includes('?') ? '?' + req.url.split('?')[1] : ''}`;
    const method = req.method.toLowerCase();

    const response = await axios({
      method,
      url,
      data: method === 'post' ? req.body : undefined,
      headers: { 'Content-Type': 'application/json' },
      responseType: req.path.includes('/download_pdf') ? 'stream' : 'json',
      params: req.query,
    });

    if (req.path.includes('/download_pdf')) {
      const safeFilename = sanitizeFilename(req.query.filename || 'report.pdf');
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', `attachment; filename="${safeFilename}"`);
      response.data.pipe(res);
    } else {
      res.json(response.data);
    }
  } catch (error) {
    console.error('Proxy error:', error.message);
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

// Serve React app for all non-API routes
app.get('*', (req, res) => {
  if (fs.existsSync(frontendPath)) {
    res.sendFile(path.join(frontendPath, 'index.html'));
  } else {
    res.send('Frontend not built yet.');
  }
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
