#!/usr/bin/env python3
"""
Script to organize existing Python files into the Flask API structure
"""

import os
import shutil
import sys
from pathlib import Path

def organize_files():
    """Organize existing Python files into proper Flask API structure"""
    
    # Get current directory (flask-api)
    current_dir = Path(__file__).parent
    print(f"Organizing files in: {current_dir}")
    
    # Create directories for existing files
    legacy_dir = current_dir / "legacy"
    models_dir = current_dir / "models"
    reference_images_dir = current_dir / "reference_images"
    
    # Create directories
    legacy_dir.mkdir(exist_ok=True)
    models_dir.mkdir(exist_ok=True)
    reference_images_dir.mkdir(exist_ok=True)
    
    # Files to move to legacy directory
    legacy_files = [
        "main.py",
        "camera.py", 
        "midas_liveness.py",
        "person_check.py",
        "test_system.py",
        "blink.py",
        "mouth_mov.py",
        "midas_wrapper.py",
        "setup.py"
    ]
    
    # Move legacy files
    for file_name in legacy_files:
        source = current_dir / file_name
        if source.exists():
            destination = legacy_dir / file_name
            shutil.move(str(source), str(destination))
            print(f"Moved {file_name} to legacy/")
    
    # Create a README in legacy directory
    legacy_readme = legacy_dir / "README.md"
    with open(legacy_readme, 'w') as f:
        f.write("""# Legacy Files

This directory contains the original Python files that were converted into the Flask API structure.

## Files:
- `main.py` - Original main liveness detection script
- `camera.py` - Camera wrapper class
- `midas_liveness.py` - MiDaS-based 2D/3D liveness detection
- `person_check.py` - Person verification using InsightFace
- `test_system.py` - System testing script
- `blink.py` - Blink and gaze detection
- `mouth_mov.py` - Voice captcha with mouth movement detection
- `midas_wrapper.py` - Wrapper for MiDaS liveness check
- `setup.py` - Setup script

## Migration:
These files have been converted into the Flask API structure:
- Services: `app/services/`
- API Endpoints: `app/api/v1/liveness.py`
- Models: `app/models.py`

The functionality is now available through REST API endpoints.
""")
    
    print(f"Created legacy/README.md")
    
    # Create models directory structure
    models_readme = models_dir / "README.md"
    with open(models_readme, 'w') as f:
        f.write("""# Models Directory

This directory should contain the required model files for liveness detection.

## Required Models:

### 1. Dlib Facial Landmark Model
- **File**: `shape_predictor_68_face_landmarks.dat`
- **Download**: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
- **Usage**: Blink detection and mouth movement analysis

### 2. Vosk Speech Recognition Model
- **File**: `vosk-model-small-en-us-0.15/`
- **Download**: https://alphacephei.com/vosk/models
- **Usage**: Voice captcha verification

### 3. InsightFace Model
- **Model**: buffalo_l (automatically downloaded)
- **Usage**: Person verification and face recognition

### 4. MiDaS Model
- **Model**: MiDaS_small (automatically downloaded via torch.hub)
- **Usage**: 2D/3D depth estimation for liveness detection

## Setup:
1. Download the dlib model and extract to this directory
2. Download the Vosk model and extract to this directory
3. Other models will be downloaded automatically on first use
""")
    
    print(f"Created models/README.md")
    
    # Create reference images directory
    reference_readme = reference_images_dir / "README.md"
    with open(reference_readme, 'w') as f:
        f.write("""# Reference Images Directory

This directory should contain reference images for person verification.

## Usage:
- Place reference images here for person verification
- Images should contain exactly one clear face
- Supported formats: JPG, PNG, JPEG
- Example: `princee.jpg` (as used in original code)

## API Usage:
When calling the person verification endpoint, provide the reference image as base64 data in the request body.
""")
    
    print(f"Created reference_images/README.md")
    
    # Create a migration guide
    migration_guide = current_dir / "MIGRATION_GUIDE.md"
    with open(migration_guide, 'w') as f:
        f.write("""# Migration Guide: From Standalone Scripts to Flask API

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
""")
    
    print(f"Created MIGRATION_GUIDE.md")
    
    print("\n✅ File organization completed!")
    print("\nNext steps:")
    print("1. Download required models to the models/ directory")
    print("2. Add reference images to reference_images/ directory")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Set up environment variables in .env")
    print("5. Run the Flask API: python run.py")

if __name__ == "__main__":
    organize_files()
