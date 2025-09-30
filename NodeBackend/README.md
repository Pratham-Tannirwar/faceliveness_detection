# FaceLive - Real-time Face Detection & Live Streaming

A modern web application for real-time face detection and live streaming using Node.js, PostgreSQL, React, and browser camera access.

## Prerequisites

- **Node.js** (>=16.0.0)
- **npm** (Node Package Manager)
- **PostgreSQL** (local or remote)
- **Browser** with camera access (works best on localhost/HTTPS)

## Features

- 🎥 Real-time camera access and video streaming
- 👤 Advanced face detection using Face-API.js
- 🔄 Live face detection with visual overlays
- 🌐 Real-time communication via Socket.IO
- 💾 PostgreSQL database integration
- 📱 Responsive design for all devices
- 🎨 Modern, beautiful UI with gradient backgrounds
- 🔐 User authentication with OTP verification
- 📋 KYC (Know Your Customer) verification system
- 👤 User profile management

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd FaceLive
npm run setup
```

This will:
- Create a `.env` file from the template
- Install all dependencies (backend and frontend)
- Set up the database

### 2. Configure Environment

Update the `.env` file with your PostgreSQL credentials:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/facelive
DB_HOST=localhost
DB_PORT=5432
DB_NAME=facelive
DB_USER=postgres
DB_PASSWORD=your_password_here

# Server Configuration
PORT=8000
NODE_ENV=development

# Security (for production)
JWT_SECRET=your_jwt_secret_here_change_in_production
SESSION_SECRET=your_session_secret_here_change_in_production
```

### 3. Start the Application

```bash
npm run dev:all
```

This starts both backend (port 8000) and frontend (port 3001).

## Manual Setup

If you prefer to set up manually:

### 1. Install Dependencies

```bash
# Backend dependencies
npm install

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Set up Environment

```bash
cp env.example .env
# Edit .env with your database credentials
```

### 3. Set up Database

```bash
npm run init-db
```

### 4. Start the Servers

```bash
# Start both frontend and backend
npm run dev:all

# Or start them separately
npm run dev:backend  # Backend only
npm run dev:frontend # Frontend only
```

## URLs

- **Frontend**: http://localhost:3001
- **Backend**: http://localhost:8000
- **API Health**: http://localhost:8000/api/health

## Usage

### User Registration & Login
1. Navigate to the signup page
2. Fill in your details and verify mobile with OTP
3. Complete registration and login
4. Access your profile and KYC verification

### Camera Access & Face Detection
1. Click "Start Camera" to begin video capture
2. Allow camera permissions when prompted
3. The video feed will appear in the main area
4. Click "Start Detection" for real-time face detection

### KYC Verification
1. Navigate to the KYC page (requires login)
2. Follow the verification instructions
3. Complete the liveness check process
4. View your verification status in the profile

### Live Streaming
1. Start the camera and detection
2. Click "Start Streaming" to begin live streaming
3. Enter a room ID to join a shared session
4. Multiple users can join the same room for collaborative viewing

## API Endpoints

### Authentication
- `POST /api/auth/send-otp` - Send OTP to mobile number
- `POST /api/auth/verify-otp` - Verify OTP
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login

### Profile
- `GET /api/profile/:userId` - Get user profile
- `GET /api/profile/:userId/kyc` - Get KYC details

### KYC
- `POST /kyc/liveness-check` - KYC liveness verification
- `POST /kyc/submit` - Submit KYC for review
- `GET /kyc/status/:userId` - Get KYC status

### Health Check
- `GET /api/health` - Server status and timestamp

### WebSocket Events

#### Client to Server
- `join-room`: Join a specific room
- `face-detection`: Send face detection data
- `stream-data`: Send live stream data

#### Server to Client
- `face-detection-update`: Receive face detection from other users
- `stream-update`: Receive stream data from other users

## Database Schema

### Users Table
- `id`: Primary key
- `fullname`: User's full name
- `email`: Unique email address
- `mobile_number`: Unique mobile number
- `password_hash`: Hashed password
- `account_number`: Unique account number
- `account_type`: Account type (standard, premium, etc.)
- `balance`: Account balance
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp

### OTP Verifications Table
- `id`: Primary key
- `mobile_number`: Mobile number for OTP
- `email`: Email address (optional)
- `otp_code`: 6-digit OTP code
- `purpose`: Purpose of OTP (signup, login, etc.)
- `is_verified`: Verification status
- `expires_at`: OTP expiration time
- `created_at`: OTP creation timestamp

### KYC Submissions Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `liveness_result`: Liveness detection result
- `status`: KYC status (pending, verified, rejected)
- `submitted_at`: Submission timestamp
- `reviewed_at`: Review timestamp
- `notes`: Additional notes

### Sessions Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `session_name`: Human-readable session name
- `room_id`: Unique room identifier
- `is_active`: Session status
- `created_at`: Session start time
- `ended_at`: Session end time

### Face Detections Table
- `id`: Primary key
- `session_id`: Foreign key to sessions table
- `user_id`: Foreign key to users table
- `face_data`: JSON data containing face detection results
- `confidence_score`: Detection confidence (0-1)
- `timestamp`: Detection timestamp

## Development

### Project Structure
```
FaceLive/
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── contexts/      # React contexts
│   │   └── services/      # API services
│   └── package.json
├── routes/                # Express routes
│   ├── auth.js           # Authentication routes
│   ├── profile.js        # Profile routes
│   └── kyc.js            # KYC routes
├── scripts/               # Database scripts
│   ├── setup-database.js # Database initialization
│   └── init-db-simple.js # Simple DB init
├── public/                # Static files
├── server.js              # Express server
├── db.js                  # Database connection
├── setup.js               # Setup script
├── package.json           # Dependencies and scripts
├── env.example            # Environment variables template
└── README.md              # This file
```

### Available Scripts

- `npm start`: Start production server
- `npm run dev`: Start development server with auto-reload
- `npm run dev:all`: Start both frontend and backend
- `npm run dev:frontend`: Start frontend only
- `npm run dev:backend`: Start backend only
- `npm run setup`: Run initial setup
- `npm run init-db`: Initialize database
- `npm run build:frontend`: Build frontend for production

### Dependencies

#### Backend Dependencies
- **express**: Web framework
- **socket.io**: Real-time communication
- **pg**: PostgreSQL client
- **cors**: Cross-origin resource sharing
- **dotenv**: Environment variable management
- **bcrypt**: Password hashing
- **multer**: File upload handling
- **sharp**: Image processing
- **face-api.js**: Face detection library

#### Frontend Dependencies
- **react**: UI library
- **react-router-dom**: Routing
- **axios**: HTTP client
- **react-webcam**: Camera access
- **cross-env**: Environment variables

#### Development Dependencies
- **nodemon**: Auto-restart development server
- **concurrently**: Run multiple commands

## Browser Compatibility

### Camera Access
- **Chrome**: Full support
- **Firefox**: Full support
- **Safari**: Full support (iOS 11+)
- **Edge**: Full support

### HTTPS Requirement
For production deployment, HTTPS is required for camera access. The application works on localhost for development.

## Troubleshooting

### Common Issues

#### Database Connection Failed
- Verify PostgreSQL is running
- Check connection credentials in `.env`
- Ensure database exists
- Run `npm run init-db` to recreate the database

#### Camera Access Denied
- Ensure you're using HTTPS in production
- Check browser permissions
- Try refreshing the page

#### Face Detection Not Working
- Check browser console for errors
- Ensure Face-API.js models are loaded
- Verify camera is working properly

#### API Calls Failing
- Check if backend server is running
- Verify API endpoints are correct
- Check browser network tab for errors

### Performance Optimization

#### For High Traffic
- Use connection pooling for PostgreSQL
- Implement Redis for session management
- Use CDN for static assets
- Optimize image compression

#### For Mobile Devices
- Reduce video resolution for mobile
- Implement adaptive quality based on device
- Use WebRTC for peer-to-peer streaming

## Security Considerations

- Use HTTPS in production
- Implement proper authentication
- Validate all input data
- Use environment variables for secrets
- Implement rate limiting
- Regular security updates
- Hash passwords with bcrypt
- Validate OTP expiration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check the troubleshooting section
- Review browser console for errors
- Ensure all prerequisites are met
- Verify database connection

---

**FaceLive** - Real-time face detection and live streaming made simple! 🚀