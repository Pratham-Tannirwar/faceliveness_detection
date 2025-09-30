const { Pool } = require('pg');
require('dotenv').config();

// Create a simple database initialization script
async function initDatabase() {
  let pool;
  
  try {
    console.log('🚀 Initializing FaceLive database...');
    
    // Database configuration
    const config = {
      user: process.env.DB_USER || 'postgres',
      host: process.env.DB_HOST || 'localhost',
      password: process.env.DB_PASSWORD || 'password',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'facelive'
    };

    console.log('📊 Configuration:', {
      host: config.host,
      port: config.port,
      database: config.database,
      user: config.user
    });
    
    // First, try to connect to the default postgres database to create our database
    const adminPool = new Pool({
      user: config.user,
      host: config.host,
      database: 'postgres', // Connect to default postgres database
      password: config.password,
      port: config.port,
    });

    // Test connection first
    await adminPool.query('SELECT NOW()');
    console.log('✅ Connected to PostgreSQL server');

    // Create the database if it doesn't exist
    try {
      await adminPool.query(`CREATE DATABASE ${config.database}`);
      console.log(`✅ Database '${config.database}' created successfully`);
    } catch (error) {
      if (error.code === '42P04') {
        console.log(`ℹ️  Database '${config.database}' already exists`);
      } else {
        throw error;
      }
    }
    
    await adminPool.end();

    // Now connect to our specific database
    pool = new Pool({
      connectionString: process.env.DATABASE_URL || `postgresql://${process.env.DB_USER || 'postgres'}:${process.env.DB_PASSWORD || 'password'}@${process.env.DB_HOST || 'localhost'}:${process.env.DB_PORT || 5432}/${process.env.DB_NAME || 'facelive'}`,
    });

    // Create users table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        fullname VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        mobile_number VARCHAR(15) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        account_number VARCHAR(20) UNIQUE,
        account_type VARCHAR(20) DEFAULT 'standard',
        balance DECIMAL(15,2) DEFAULT 0.00,
        is_verified BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Ensure is_verified column exists on users
    await pool.query(`
      DO $$
      BEGIN
        IF NOT EXISTS (
          SELECT 1 FROM information_schema.columns 
          WHERE table_name='users' AND column_name='is_verified'
        ) THEN
          ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
        END IF;
      END$$;
    `);

    // Create sessions table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        session_name VARCHAR(100) NOT NULL,
        room_id VARCHAR(50) UNIQUE NOT NULL,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP
      )
    `);

    // Create face_detections table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS face_detections (
        id SERIAL PRIMARY KEY,
        session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        face_data JSONB,
        confidence_score DECIMAL(5,4),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create kyc_submissions table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS kyc_submissions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        liveness_result VARCHAR(20) DEFAULT 'pending',
        status VARCHAR(20) DEFAULT 'pending',
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TIMESTAMP,
        notes TEXT
      )
    `);

    // Create otp_verifications table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS otp_verifications (
        id SERIAL PRIMARY KEY,
        mobile_number VARCHAR(15) NOT NULL,
        email VARCHAR(100),
        otp_code VARCHAR(6) NOT NULL,
        purpose VARCHAR(20) NOT NULL,
        is_verified BOOLEAN DEFAULT FALSE,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create indexes for better performance
    await pool.query(`
      CREATE INDEX IF NOT EXISTS idx_sessions_room_id ON sessions(room_id);
      CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
      CREATE INDEX IF NOT EXISTS idx_face_detections_session_id ON face_detections(session_id);
      CREATE INDEX IF NOT EXISTS idx_face_detections_timestamp ON face_detections(timestamp);
      CREATE INDEX IF NOT EXISTS idx_kyc_submissions_user_id ON kyc_submissions(user_id);
      CREATE INDEX IF NOT EXISTS idx_kyc_submissions_status ON kyc_submissions(status);
      CREATE INDEX IF NOT EXISTS idx_otp_mobile_number ON otp_verifications(mobile_number);
      CREATE INDEX IF NOT EXISTS idx_otp_expires_at ON otp_verifications(expires_at);
    `);

    console.log('Database initialization completed successfully!');
    console.log('Tables created: users, sessions, face_detections, kyc_submissions, otp_verifications');
    
  } catch (error) {
    if (error.code === '42P04') {
      console.log('Database already exists, continuing with table creation...');
      // Database exists, continue with table creation
      pool = new Pool({
        connectionString: process.env.DATABASE_URL || `postgresql://${process.env.DB_USER || 'postgres'}:${process.env.DB_PASSWORD || 'password'}@${process.env.DB_HOST || 'localhost'}:${process.env.DB_PORT || 5432}/${process.env.DB_NAME || 'facelive'}`,
      });
      
      // Continue with table creation...
      await pool.query(`
        CREATE TABLE IF NOT EXISTS users (
          id SERIAL PRIMARY KEY,
          fullname VARCHAR(100) NOT NULL,
          email VARCHAR(100) UNIQUE NOT NULL,
          mobile_number VARCHAR(15) UNIQUE NOT NULL,
          password_hash VARCHAR(255) NOT NULL,
          account_number VARCHAR(20) UNIQUE,
          account_type VARCHAR(20) DEFAULT 'standard',
          balance DECIMAL(15,2) DEFAULT 0.00,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);

      await pool.query(`
        CREATE TABLE IF NOT EXISTS otp_verifications (
          id SERIAL PRIMARY KEY,
          mobile_number VARCHAR(15) NOT NULL,
          email VARCHAR(100),
          otp_code VARCHAR(6) NOT NULL,
          purpose VARCHAR(20) NOT NULL,
          is_verified BOOLEAN DEFAULT FALSE,
          expires_at TIMESTAMP NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);

      console.log('Tables created successfully!');
    } else {
      console.error('Error initializing database:', error);
      process.exit(1);
    }
  } finally {
    if (pool) {
      await pool.end();
    }
  }
}

initDatabase();
