# Legacy Files

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
