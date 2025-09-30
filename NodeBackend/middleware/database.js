const { query } = require('../db');

// Database health check middleware
const checkDatabaseHealth = async (req, res, next) => {
  try {
    // Simple query to test database connection
    await query('SELECT 1 as health_check');
    next();
  } catch (error) {
    console.error('Database health check failed:', error.message);
    res.status(503).json({
      success: false,
      error: 'Database connection failed',
      message: 'Service temporarily unavailable'
    });
  }
};

// Database connection status endpoint
const getDatabaseStatus = async (req, res) => {
  try {
    const start = Date.now();
    const result = await query('SELECT NOW() as current_time, version() as postgres_version');
    const duration = Date.now() - start;
    
    res.json({
      success: true,
      status: 'connected',
      response_time: `${duration}ms`,
      timestamp: result.rows[0].current_time,
      version: result.rows[0].postgres_version.split(' ')[0],
      message: 'Database is healthy'
    });
  } catch (error) {
    console.error('Database status check failed:', error.message);
    res.status(503).json({
      success: false,
      status: 'disconnected',
      error: error.message,
      message: 'Database is not accessible'
    });
  }
};

// Table existence check
const checkTables = async (req, res) => {
  try {
    const tables = await query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name
    `);
    
    const expectedTables = ['users', 'otp_verifications', 'sessions', 'face_detections', 'kyc_submissions'];
    const existingTables = tables.rows.map(row => row.table_name);
    const missingTables = expectedTables.filter(table => !existingTables.includes(table));
    
    res.json({
      success: true,
      tables: {
        existing: existingTables,
        expected: expectedTables,
        missing: missingTables,
        count: existingTables.length
      },
      status: missingTables.length === 0 ? 'complete' : 'incomplete'
    });
  } catch (error) {
    console.error('Table check failed:', error.message);
    res.status(500).json({
      success: false,
      error: error.message,
      message: 'Failed to check tables'
    });
  }
};

module.exports = {
  checkDatabaseHealth,
  getDatabaseStatus,
  checkTables
};
