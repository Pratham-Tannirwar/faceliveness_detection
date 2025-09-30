#!/usr/bin/env python3
"""
Setup script for FaceLive Flask API
"""

import os
import sys
import subprocess
import urllib.request
import bz2
import zipfile
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"[RUNNING] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def download_file(url, destination, description):
    """Download a file from URL"""
    print(f"[DOWNLOADING] {description}...")
    try:
        urllib.request.urlretrieve(url, destination)
        print(f"[SUCCESS] {description} completed successfully")
        return True
    except Exception as e:
        print(f"[ERROR] {description} failed: {e}")
        return False

def extract_bz2(bz2_path, extract_path):
    """Extract bz2 file"""
    print(f"[EXTRACTING] {bz2_path}...")
    try:
        with bz2.open(bz2_path, 'rb') as f_in:
            with open(extract_path, 'wb') as f_out:
                f_out.write(f_in.read())
        os.remove(bz2_path)
        print(f"[SUCCESS] Extraction completed successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return False

def setup_flask_api():
    """Main setup function"""
    print("[STARTING] Setting up FaceLive Flask API")
    print("=" * 50)
    
    # Get current directory
    current_dir = Path(__file__).parent
    models_dir = current_dir / "models"
    reference_images_dir = current_dir / "reference_images"
    
    # Create directories
    models_dir.mkdir(exist_ok=True)
    reference_images_dir.mkdir(exist_ok=True)
    
    # Step 1: Install Python dependencies
    print("\n[STEP 1] Installing Python dependencies")
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        print("[ERROR] Failed to install dependencies. Please check your Python environment.")
        return False
    
    # Step 2: Download required models
    print("\n[STEP 2] Downloading required models")
    
    # Download dlib facial landmark model
    dlib_model_path = models_dir / "shape_predictor_68_face_landmarks.dat"
    if not dlib_model_path.exists():
        dlib_bz2_path = models_dir / "shape_predictor_68_face_landmarks.dat.bz2"
        if download_file(
            "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2",
            str(dlib_bz2_path),
            "Downloading dlib facial landmark model"
        ):
            extract_bz2(str(dlib_bz2_path), str(dlib_model_path))
    else:
        print("[SUCCESS] Dlib facial landmark model already exists")
    
    # Download Vosk speech recognition model
    vosk_model_dir = models_dir / "vosk-model-small-en-us-0.15"
    if not vosk_model_dir.exists():
        vosk_zip_path = models_dir / "vosk-model-small-en-us-0.15.zip"
        if download_file(
            "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            str(vosk_zip_path),
            "Downloading Vosk speech recognition model"
        ):
            print("[EXTRACTING] Extracting Vosk model...")
            try:
                with zipfile.ZipFile(vosk_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(models_dir)
                os.remove(vosk_zip_path)
                print("[SUCCESS] Vosk model extraction completed")
            except Exception as e:
                print(f"[ERROR] Vosk model extraction failed: {e}")
    else:
        print("[SUCCESS] Vosk speech recognition model already exists")
    
    # Step 3: Set up environment variables
    print("\nStep 3: Setting up environment variables")
    env_file = current_dir / ".env"
    env_example = current_dir / "env.example"
    
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(str(env_example), str(env_file))
        print("Created .env file from env.example")
        print("Please edit .env file with your specific configuration")
    elif env_file.exists():
        print(".env file already exists")
    else:
        print("No env.example found, please create .env file manually")
    
    # Step 4: Test system components
    print("\nStep 4: Testing system components")
    
    # Test Python imports
    test_imports = [
        "cv2",
        "numpy", 
        "torch",
        "mediapipe",
        "dlib",
        "vosk",
        "sounddevice",
        "insightface"
    ]
    
    failed_imports = []
    for module in test_imports:
        try:
            __import__(module)
            print(f"{module} import successful")
        except ImportError as e:
            print(f"{module} import failed: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\nSome modules failed to import: {failed_imports}")
        print("You may need to install additional dependencies or check your Python environment")
    
    # Step 5: Create sample reference image directory
    print("\nStep 5: Setting up reference images")
    sample_readme = reference_images_dir / "README.md"
    if not sample_readme.exists():
        with open(sample_readme, 'w') as f:
            f.write("""# Reference Images

Place reference images here for person verification.

## Requirements:
- Images should contain exactly one clear face
- Supported formats: JPG, PNG, JPEG
- Recommended size: 300x300 to 800x800 pixels

## Usage:
When calling the person verification API endpoint, provide the reference image as base64 data.
""")
        print("reated reference images directory with README")
    
    # Step 6: Database setup (if needed)
    print("\nStep 6: Database setup")
    print("Database setup will be handled by the main application")
    print("Make sure PostgreSQL is running and accessible")
    
    # Final summary
    print("\n" + "=" * 50)
    print("Flask API setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your database and configuration settings")
    print("2. Ensure PostgreSQL database is running")
    print("3. Add reference images to reference_images/ directory")
    print("4. Run database migrations: flask db upgrade")
    print("5. Start the API: python run.py")
    print("\nDocumentation:")
    print("- API Documentation: http://localhost:5000/api/v1/docs/")
    print("- Migration Guide: MIGRATION_GUIDE.md")
    print("- Legacy Files: legacy/README.md")
    
    return True

if __name__ == "__main__":
    success = setup_flask_api()
    sys.exit(0 if success else 1)
