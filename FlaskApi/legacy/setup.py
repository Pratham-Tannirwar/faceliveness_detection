#!/usr/bin/env python3
"""
Setup script for Liveness Detection System
Downloads required models and sets up the environment
"""

import os
import urllib.request
import bz2
import zipfile
import sys

def download_file(url, destination, description):
    """Download a file with progress indication"""
    print(f"⬇ Downloading {description}...")
    try:
        urllib.request.urlretrieve(url, destination)
        print(f"{description} downloaded successfully")
        return True
    except Exception as e:
        print(f"Failed to download {description}: {e}")
        return False

def extract_bz2(compressed_file, output_file):
    """Extract bz2 compressed file"""
    try:
        with bz2.open(compressed_file) as f_in, open(output_file, "wb") as f_out:
            f_out.write(f_in.read())
        os.remove(compressed_file)
        return True
    except Exception as e:
        print(f"Failed to extract {compressed_file}: {e}")
        return False

def setup_dlib_model():
    """Download and setup dlib facial landmark predictor"""
    model_path = "shape_predictor_68_face_landmarks.dat"
    if os.path.exists(model_path):
        print("Dlib model already exists")
        return True
    
    url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
    temp_file = "sp.dat.bz2"
    
    if download_file(url, temp_file, "Dlib facial landmark predictor"):
        return extract_bz2(temp_file, model_path)
    return False

def setup_vosk_model():
    """Download and setup Vosk speech recognition model"""
    model_dir = "vosk-model-small-en-us-0.15"
    if os.path.exists(model_dir):
        print("Vosk model already exists")
        return True
    
    url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    temp_file = "vosk-model-small-en-us-0.15.zip"
    
    if download_file(url, temp_file, "Vosk speech recognition model"):
        try:
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove(temp_file)
            print("Vosk model extracted successfully")
            return True
        except Exception as e:
            print(f"Failed to extract Vosk model: {e}")
            return False
    return False

def check_reference_image():
    """Check if reference image exists"""
    ref_dir = "reference_images"
    ref_image = os.path.join(ref_dir, "princee.jpg")
    
    if not os.path.exists(ref_dir):
        os.makedirs(ref_dir)
        print(f"Created directory: {ref_dir}")
    
    if not os.path.exists(ref_image):
        print(f"Reference image not found: {ref_image}")
        print("Please add your reference image named 'princee.jpg' to the reference_images folder")
        return False
    else:
        print("Reference image found")
        return True

def main():
    """Main setup function"""
    print("Setting up Liveness Detection System...")
    print("=" * 50)
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    print(f"Working directory: {current_dir}")
    
    # Setup models
    success = True
    
    print("\nSetting up required models...")
    if not setup_dlib_model():
        success = False
    
    if not setup_vosk_model():
        success = False
    
    # Check reference image
    print("\n🔍 Checking reference image...")
    if not check_reference_image():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("Setup completed successfully!")
        print("\nTo run the liveness detection system:")
        print("python main.py")
    else:
        print("Setup completed with warnings!")
        print("Please check the messages above and fix any issues.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)