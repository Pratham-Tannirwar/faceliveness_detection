const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'facelive',
  password: process.env.DB_PASSWORD || 'password',
  port: process.env.DB_PORT || 5432,
});

async function setupDatabase() {
  try {
    console.log('Setting up FaceLive database...');

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

    console.log('Database setup completed successfully!');
    console.log('Tables created: users, sessions, face_detections, kyc_submissions, otp_verifications');
    
  } catch (error) {
    console.error('Error setting up database:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

setupDatabase();

