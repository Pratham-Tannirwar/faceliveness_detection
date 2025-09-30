# FaceLive Flask API

A Python Flask-based API for the FaceLive application, providing face detection, live streaming, and KYC verification services.

## Features

- **Authentication**: JWT-based authentication with OTP verification
- **Face Detection**: Real-time face detection using OpenCV
- **Live Streaming**: Session management for live streaming
- **KYC Verification**: Know Your Customer verification with liveness detection
- **User Management**: User profile and account management
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /login` - User login
- `POST /signup` - User registration
- `POST /send-otp` - Send OTP to mobile number
- `POST /verify-otp` - Verify OTP code
- `POST /refresh` - Refresh access token
- `POST /logout` - User logout

### Users (`/api/v1/users`)
- `GET /profile` - Get current user profile
- `PUT /profile` - Update user profile
- `GET /<user_id>` - Get user by ID
- `POST /change-password` - Change user password

### Sessions (`/api/v1/sessions`)
- `GET /` - Get user's sessions
- `POST /` - Create a new session
- `GET /<session_id>` - Get session by ID
- `DELETE /<session_id>` - End a session
- `POST /join/<room_id>` - Join session by room ID
- `GET /active` - Get active sessions

### Face Detection (`/api/v1/face-detection`)
- `POST /detect` - Perform face detection
- `GET /session/<session_id>` - Get session detections
- `GET /<detection_id>` - Get detection by ID
- `POST /liveness-check` - Perform liveness detection
- `GET /stats/<session_id>` - Get detection statistics

### KYC (`/api/v1/kyc`)
- `GET /status` - Get KYC status
- `POST /submit` - Submit KYC documents
- `POST /liveness-check` - Perform KYC liveness check
- `GET /history` - Get KYC history
- `GET /requirements` - Get KYC requirements

## Setup and Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis (optional, for caching)

### Installation

1. **Clone and navigate to the Flask API directory:**
   ```bash
   cd flask-api
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database:**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application:**
   ```bash
   python app.py
   ```

### Docker Setup

1. **Build the Docker image:**
   ```bash
   docker build -t facelive-flask-api .
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Flask secret key | Required |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `REDIS_URL` | Redis connection string | Optional |

### Database Configuration

The API uses the same PostgreSQL database as the Node.js backend. Make sure the database is running and accessible.

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- **Swagger UI**: http://localhost:5000/api/v1/docs/
- **ReDoc**: http://localhost:5000/api/v1/docs/redoc/

## Development

### Project Structure

```
flask-api/
├── app/
│   ├── api/
│   │   └── v1/           # API version 1
│   ├── config/           # Configuration files
│   ├── middleware/       # Custom middleware
│   ├── models/           # Database models
│   ├── services/         # Business logic
│   └── utils/            # Utility functions
├── logs/                 # Application logs
├── migrations/           # Database migrations
├── static/              # Static files
├── templates/           # HTML templates
├── tests/               # Test files
├── app.py               # Main application file
├── requirements.txt     # Python dependencies
└── Dockerfile          # Docker configuration
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black app/
flake8 app/
```

## Integration with Node.js Backend

This Flask API is designed to work alongside the existing Node.js backend:

- **Shared Database**: Both APIs use the same PostgreSQL database
- **CORS Configuration**: Configured to allow requests from the Node.js backend
- **Port Configuration**: Runs on port 5000 (different from Node.js on port 8000)

### API Communication

The Flask API can be called from the Node.js backend or directly from the frontend:

```javascript
// Example: Call Flask API from frontend
const response = await fetch('http://localhost:5000/api/v1/face-detection/detect', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    session_id: 1,
    image_data: base64ImageData
  })
});
```

## Production Deployment

### Using Gunicorn

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
```

### Using Docker

```bash
docker run -p 5000:5000 facelive-flask-api
```

### Environment Variables for Production

Make sure to set these environment variables in production:
- `FLASK_ENV=production`
- `FLASK_DEBUG=False`
- `SECRET_KEY` (strong, random key)
- `JWT_SECRET_KEY` (strong, random key)
- `DATABASE_URL` (production database URL)

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify database credentials in `.env`
   - Ensure database exists

2. **OpenCV Installation Issues**
   - Install system dependencies: `apt-get install libgl1-mesa-glx libglib2.0-0`
   - Use the provided Dockerfile for consistent environment

3. **JWT Token Issues**
   - Check `JWT_SECRET_KEY` is set
   - Verify token expiration settings

### Logs

Check application logs in the `logs/` directory for detailed error information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details
