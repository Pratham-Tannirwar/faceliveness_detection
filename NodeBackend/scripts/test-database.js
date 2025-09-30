const { Pool } = require('pg');
require('dotenv').config();

async function testDatabase() {
  let pool;
  
  try {
    console.log('🧪 Testing database connection...');
    
    // Test configuration
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
      user: config.user,
      password: config.password ? '***' : 'undefined'
    });

    // Create connection pool - first try connecting to postgres database
    pool = new Pool({
      user: config.user,
      host: config.host,
      password: config.password,
      port: config.port,
      database: 'postgres' // Connect to default postgres database first
    });

    // Test basic connection
    console.log('\n1️⃣ Testing basic connection...');
    const result = await pool.query('SELECT NOW() as current_time, version() as postgres_version');
    console.log('✅ Connection successful');
    console.log(`   Time: ${result.rows[0].current_time}`);
    console.log(`   PostgreSQL: ${result.rows[0].postgres_version.split(' ')[0]}`);

    // Test table existence
    console.log('\n2️⃣ Checking tables...');
    const tables = await pool.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name
    `);

    const expectedTables = ['users', 'otp_verifications', 'sessions', 'face_detections', 'kyc_submissions'];
    const existingTables = tables.rows.map(row => row.table_name);
    
    console.log('📋 Found tables:', existingTables);
    
    const missingTables = expectedTables.filter(table => !existingTables.includes(table));
    if (missingTables.length > 0) {
      console.log('⚠️  Missing tables:', missingTables);
      console.log('💡 Run: npm run setup-db-complete');
    } else {
      console.log('✅ All required tables exist');
    }

    // Test table structure
    console.log('\n3️⃣ Testing table structure...');
    for (const table of expectedTables) {
      if (existingTables.includes(table)) {
        const columns = await pool.query(`
          SELECT column_name, data_type, is_nullable
          FROM information_schema.columns
          WHERE table_name = $1
          ORDER BY ordinal_position
        `, [table]);
        
        console.log(`   ${table}: ${columns.rows.length} columns`);
      }
    }

    // Test sample queries
    console.log('\n4️⃣ Testing sample queries...');
    
    // Test users table
    const userCount = await pool.query('SELECT COUNT(*) as count FROM users');
    console.log(`   Users: ${userCount.rows[0].count} records`);
    
    // Test OTP table
    const otpCount = await pool.query('SELECT COUNT(*) as count FROM otp_verifications');
    console.log(`   OTP verifications: ${otpCount.rows[0].count} records`);
    
    // Test KYC table
    const kycCount = await pool.query('SELECT COUNT(*) as count FROM kyc_submissions');
    console.log(`   KYC submissions: ${kycCount.rows[0].count} records`);

    console.log('\n✅ Database test completed successfully!');
    console.log('\n🚀 You can now start the application with:');
    console.log('   npm run dev:all');

  } catch (error) {
    console.error('\n❌ Database test failed:', error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.log('\n💡 Troubleshooting:');
      console.log('   - PostgreSQL is not running');
      console.log('   - Check if port 5432 is available');
      console.log('   - Start PostgreSQL service');
    } else if (error.code === '28P01') {
      console.log('\n💡 Troubleshooting:');
      console.log('   - Wrong password');
      console.log('   - Check your .env file');
    } else if (error.code === '3D000') {
      console.log('\n💡 Troubleshooting:');
      console.log('   - Database does not exist');
      console.log('   - Run: npm run setup-db-complete');
    } else {
      console.log('\n💡 Troubleshooting:');
      console.log('   - Check your database configuration');
      console.log('   - Verify PostgreSQL is installed and running');
    }
    
    process.exit(1);
  } finally {
    if (pool) {
      await pool.end();
    }
  }
}

// Run the test
testDatabase();
