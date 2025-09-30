const { Pool } = require('pg');
require('dotenv').config();

// Database configuration
const config = {
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  password: process.env.DB_PASSWORD || 'password',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'facelive'
};

async function setupDatabase() {
  let adminPool;
  let appPool;
  
  try {
    console.log('🚀 Starting FaceLive database setup...');
    console.log('📊 Configuration:', {
      host: config.host,
      port: config.port,
      database: config.database,
      user: config.user
    });

    // Step 1: Connect to PostgreSQL server (not specific database)
    console.log('\n1️⃣ Connecting to PostgreSQL server...');
    adminPool = new Pool({
      user: config.user,
      host: config.host,
      password: config.password,
      port: config.port,
      database: 'postgres' // Connect to default postgres database
    });

    // Test connection
    await adminPool.query('SELECT NOW()');
    console.log('✅ Connected to PostgreSQL server');

    // Step 2: Create database if it doesn't exist
    console.log('\n2️⃣ Creating database...');
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

    // Close admin connection
    await adminPool.end();
    adminPool = null;

    // Step 3: Connect to our specific database
    console.log('\n3️⃣ Connecting to application database...');
    appPool = new Pool({
      user: config.user,
      host: config.host,
      password: config.password,
      port: config.port,
      database: config.database
    });

    // Test connection
    await appPool.query('SELECT NOW()');
    console.log('✅ Connected to application database');

    // Step 4: Create tables
    console.log('\n4️⃣ Creating tables...');

    // Users table
    await appPool.query(`
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
    console.log('✅ Users table created');

    // Ensure is_verified column exists on users
    await appPool.query(`
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

    // OTP verifications table
    await appPool.query(`
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
    console.log('✅ OTP verifications table created');

    // Sessions table
    await appPool.query(`
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
    console.log('✅ Sessions table created');

    // Face detections table
    await appPool.query(`
      CREATE TABLE IF NOT EXISTS face_detections (
        id SERIAL PRIMARY KEY,
        session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        face_data JSONB,
        confidence_score DECIMAL(5,4),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    console.log('✅ Face detections table created');

    // KYC submissions table
    await appPool.query(`
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
    console.log('✅ KYC submissions table created');

    // Step 5: Create indexes
    console.log('\n5️⃣ Creating indexes...');
    const indexes = [
      'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
      'CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile_number)',
      'CREATE INDEX IF NOT EXISTS idx_users_account_number ON users(account_number)',
      'CREATE INDEX IF NOT EXISTS idx_otp_mobile_number ON otp_verifications(mobile_number)',
      'CREATE INDEX IF NOT EXISTS idx_otp_expires_at ON otp_verifications(expires_at)',
      'CREATE INDEX IF NOT EXISTS idx_sessions_room_id ON sessions(room_id)',
      'CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_face_detections_session_id ON face_detections(session_id)',
      'CREATE INDEX IF NOT EXISTS idx_face_detections_timestamp ON face_detections(timestamp)',
      'CREATE INDEX IF NOT EXISTS idx_kyc_submissions_user_id ON kyc_submissions(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_kyc_submissions_status ON kyc_submissions(status)'
    ];

    for (const indexQuery of indexes) {
      await appPool.query(indexQuery);
    }
    console.log('✅ Indexes created');

    // Step 6: Insert sample data (optional)
    console.log('\n6️⃣ Checking for sample data...');
    const userCount = await appPool.query('SELECT COUNT(*) FROM users');
    if (userCount.rows[0].count === '0') {
      console.log('📝 No users found, skipping sample data');
    } else {
      console.log(`ℹ️  Found ${userCount.rows[0].count} existing users`);
    }

    // Step 7: Verify setup
    console.log('\n7️⃣ Verifying setup...');
    const tables = await appPool.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name
    `);
    
    console.log('📋 Created tables:');
    tables.rows.forEach(row => {
      console.log(`   - ${row.table_name}`);
    });

    console.log('\n🎉 Database setup completed successfully!');
    console.log('\n📊 Database Summary:');
    console.log(`   Host: ${config.host}:${config.port}`);
    console.log(`   Database: ${config.database}`);
    console.log(`   User: ${config.user}`);
    console.log(`   Tables: ${tables.rows.length}`);

  } catch (error) {
    console.error('\n❌ Database setup failed:', error.message);
    console.error('Error details:', error);
    
    if (error.code === 'ECONNREFUSED') {
      console.log('\n💡 Troubleshooting:');
      console.log('   - Make sure PostgreSQL is running');
      console.log('   - Check if the port 5432 is available');
      console.log('   - Verify your database credentials');
    } else if (error.code === '28P01') {
      console.log('\n💡 Troubleshooting:');
      console.log('   - Check your database password');
      console.log('   - Verify the username is correct');
    }
    
    process.exit(1);
  } finally {
    try {
      if (adminPool) {
        await adminPool.end();
      }
    } catch (e) {}
    try {
      if (appPool) {
        await appPool.end();
      }
    } catch (e) {}
  }
}

// Run the setup
setupDatabase();
