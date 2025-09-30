#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Setting up FaceLive project...\n');

// Check if .env file exists
const envPath = path.join(__dirname, '.env');
if (!fs.existsSync(envPath)) {
  console.log('📝 Creating .env file from template...');
  try {
    const envExample = fs.readFileSync(path.join(__dirname, 'env.example'), 'utf8');
    fs.writeFileSync(envPath, envExample);
    console.log('✅ .env file created successfully');
  } catch (error) {
    console.log('❌ Failed to create .env file:', error.message);
    console.log('Please manually copy env.example to .env and update the values');
  }
} else {
  console.log('✅ .env file already exists');
}

// Install backend dependencies
console.log('\n📦 Installing backend dependencies...');
try {
  execSync('npm install', { stdio: 'inherit', cwd: __dirname });
  console.log('✅ Backend dependencies installed');
} catch (error) {
  console.log('❌ Failed to install backend dependencies:', error.message);
}

// Install frontend dependencies
console.log('\n📦 Installing frontend dependencies...');
try {
  execSync('npm install', { stdio: 'inherit', cwd: path.join(__dirname, 'frontend') });
  console.log('✅ Frontend dependencies installed');
} catch (error) {
  console.log('❌ Failed to install frontend dependencies:', error.message);
}

// Test database connection first
console.log('\n🧪 Testing database connection...');
try {
  execSync('node scripts/test-database.js', { stdio: 'inherit', cwd: __dirname });
  console.log('✅ Database connection test passed');
} catch (error) {
  console.log('❌ Database connection test failed');
  console.log('\n💡 Database Setup Options:');
  console.log('1. Docker (Recommended):');
  console.log('   docker run --name facelive-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=facelive -p 5432:5432 -d postgres:15');
  console.log('2. Docker Compose:');
  console.log('   docker-compose up -d');
  console.log('3. Manual PostgreSQL installation');
  console.log('\nAfter setting up PostgreSQL, run:');
  console.log('   npm run setup-db-complete');
}

// Setup database if connection test passed
console.log('\n🗄️ Setting up database...');
try {
  execSync('node scripts/setup-database-complete.js', { stdio: 'inherit', cwd: __dirname });
  console.log('✅ Database setup completed');
} catch (error) {
  console.log('❌ Database setup failed:', error.message);
  console.log('Please make sure PostgreSQL is running and try again');
}

console.log('\n🎉 Setup completed!');
console.log('\n📋 Next steps:');
console.log('1. Make sure PostgreSQL is running');
console.log('2. Run "npm run test-db" to verify database setup');
console.log('3. Run "npm run dev:all" to start both frontend and backend');
console.log('4. Or run "npm start" for backend only and "npm run dev:frontend" for frontend only');
console.log('\n🔗 URLs:');
console.log('- Backend: http://localhost:8000');
console.log('- Frontend: http://localhost:3001');
console.log('- API Health: http://localhost:8000/api/health');
console.log('- Database Health: http://localhost:8000/api/db/health');
console.log('- Database Tables: http://localhost:8000/api/db/tables');
