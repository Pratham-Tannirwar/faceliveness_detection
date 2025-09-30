const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Database connection using db.js module
const { query, pool } = require('./db');

// Test database connection
pool.on('connect', () => {
  console.log('Connected to PostgreSQL database');
});

pool.on('error', (err) => {
  console.error('Database connection error:', err);
  console.log('Server will continue without database connection');
});

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Import routes
const authRoutes = require('./routes/auth');
const profileRoutes = require('./routes/profile');
const kycRoutes = require('./routes/kyc');

// Import middleware
const { checkDatabaseHealth, getDatabaseStatus, checkTables } = require('./middleware/database');

// API Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Database health check routes
app.get('/api/db/health', getDatabaseStatus);
app.get('/api/db/tables', checkTables);

// Use auth routes with database health check
app.use('/api/auth', checkDatabaseHealth, authRoutes);

// Use profile routes
app.use('/api', profileRoutes);

// Use KYC routes
app.use('/kyc', kycRoutes);

// Socket.IO for real-time communication
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  socket.on('join-room', (roomId) => {
    socket.join(roomId);
    console.log(`User ${socket.id} joined room ${roomId}`);
  });

  socket.on('face-detection', (data) => {
    // Broadcast face detection data to all clients in the room
    socket.to(data.roomId).emit('face-detection-update', data);
  });

  socket.on('stream-data', (data) => {
    // Handle live stream data
    socket.to(data.roomId).emit('stream-update', data);
  });

  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

const PORT = process.env.PORT || 8000;

server.listen(PORT, () => {
  console.log(`FaceLive server running on port ${PORT}`);
  console.log(`Access the application at: http://localhost:${PORT}`);
  console.log('Make sure to run on HTTPS for camera access in production');
});

// Export app for testing
module.exports = app;
