# Migration Guide: From Standalone Scripts to Flask API

This guide explains how to migrate from the original Python scripts to the new Flask API structure.

## Original vs New Structure

### Original Files (now in `legacy/`):
- `main.py` - Complete liveness detection sequence
- `camera.py` - Camera wrapper
- `midas_liveness.py` - 2D/3D liveness detection
- `person_check.py` - Person verification
- `blink.py` - Blink detection
- `mouth_mov.py` - Voice captcha
- `test_system.py` - System testing

### New Flask API Structure:
- `app/services/` - Business logic services
- `app/api/v1/` - REST API endpoints
- `app/models.py` - Database models
- `app/config.py` - Configuration

## API Endpoints

### Complete Liveness Detection
**Original**: `python main.py`
**New**: `POST /api/v1/liveness/complete`

```json
{
  "reference_image": "base64_encoded_image",
  "enable_display": false
}
```

### Individual Steps

#### Person Verification
**Original**: `PersonVerificationAndMonitor` class
**New**: `POST /api/v1/liveness/person-verification`

#### 2D/3D Liveness Check
**Original**: `run_2d_3d_liveness_check()` function
**New**: `POST /api/v1/liveness/2d-3d-check`

#### Blink Detection
**Original**: `blink()` function
**New**: `POST /api/v1/liveness/blink-detection`

#### Voice Captcha
**Original**: `mouth_captcha_verification()` function
**New**: `POST /api/v1/liveness/voice-captcha`

### System Status
**Original**: `python test_system.py`
**New**: `GET /api/v1/liveness/status`

## Key Changes

1. **Authentication**: All endpoints now require JWT authentication
2. **Session Management**: Each detection creates a database session
3. **Error Handling**: Comprehensive error handling and logging
4. **Configuration**: Centralized configuration management
5. **Database Integration**: Results stored in PostgreSQL database
6. **API Documentation**: Auto-generated Swagger documentation

## Setup Requirements

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables in `.env`
3. Download required models to `models/` directory
4. Run database migrations: `flask db upgrade`
5. Start the API: `python run.py`

## Testing

Test the API using the interactive documentation at:
- Swagger UI: `http://localhost:5000/api/v1/docs/`
- System Status: `GET /api/v1/liveness/status`
- System Test: `GET /api/v1/liveness/test`
