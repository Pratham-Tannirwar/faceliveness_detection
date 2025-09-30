const { Pool } = require('pg');

// Test with minimal configuration
const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'postgres',
  user: 'postgres'
  // No password field at all
});

async function test() {
  try {
    console.log('Testing simple connection...');
    const result = await pool.query('SELECT NOW() as current_time');
    console.log('✅ Connection successful:', result.rows[0]);
  } catch (error) {
    console.error('❌ Connection failed:', error.message);
  } finally {
    await pool.end();
  }
}

test();
