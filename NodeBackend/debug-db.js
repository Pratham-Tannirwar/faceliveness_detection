const { Pool } = require('pg');
require('dotenv').config();

console.log('Environment variables:');
console.log('DB_USER:', process.env.DB_USER);
console.log('DB_PASSWORD:', process.env.DB_PASSWORD);
console.log('DB_HOST:', process.env.DB_HOST);
console.log('DB_PORT:', process.env.DB_PORT);
console.log('DB_NAME:', process.env.DB_NAME);

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres@localhost:5432/postgres'
});

async function testConnection() {
  try {
    console.log('Testing connection...');
    const result = await pool.query('SELECT NOW() as current_time');
    console.log('✅ Connection successful:', result.rows[0]);
  } catch (error) {
    console.error('❌ Connection failed:', error.message);
    console.error('Error code:', error.code);
  } finally {
    await pool.end();
  }
}

testConnection();
