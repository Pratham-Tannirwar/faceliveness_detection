# Models Directory

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
