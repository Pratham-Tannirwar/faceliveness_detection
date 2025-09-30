#!/usr/bin/env python3
"""
Test script to verify liveness detection system components
"""

import cv2
import os
import sys

def test_camera():
    """Test camera functionality"""
    print("Testing camera...")
    try:
        from camera import Camera
        cam = Camera(0)
        frame = cam.get_frame()
        if frame is not None:
            print(f"Camera working! Frame shape: {frame.shape}")
            cam.release()
            return True
        else:
            print("Camera returned None frame")
            return False
    except Exception as e:
        print(f"Camera test failed: {e}")
        return False

def test_models():
    """Test if required models exist"""
    print("Testing required models...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check dlib model
    dlib_model = os.path.join(current_dir, "shape_predictor_68_face_landmarks.dat")
    if os.path.exists(dlib_model):
        print("Dlib facial landmark model found")
    else:
        print("Dlib facial landmark model missing")
        return False
    
    # Check vosk model
    vosk_model = os.path.join(current_dir, "vosk-model-small-en-us-0.15")
    if os.path.exists(vosk_model):
        print("Vosk speech recognition model found")
    else:
        print("Vosk speech recognition model missing")
        return False
    
    # Check reference image
    ref_image = os.path.join(current_dir, "reference_images", "princee.jpg")
    if os.path.exists(ref_image):
        print("Reference image found")
    else:
        print("Reference image not found (add princee.jpg to reference_images/)")
    
    return True

def test_face_detection():
    """Test basic face detection"""
    print("Testing face detection...")
    try:
        import cv2
        from camera import Camera
        
        cam = Camera(0)
        frame = cam.get_frame()
        cam.release()
        
        if frame is not None:
            # Simple face detection test
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                print(f"Face detection working! Found {len(faces)} face(s)")
                return True
            else:
                print("No faces detected in test frame (this is normal if no face is visible)")
                return True
        else:
            print("No frame available for face detection test")
            return False
            
    except Exception as e:
        print(f"Face detection test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running Liveness Detection System Tests")
    print("=" * 50)
    
    tests = [
        ("Models", test_models),
        ("Camera", test_camera),
        ("Face Detection", test_face_detection)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\nAll tests passed! System is ready to use.")
        print("Run 'python main.py' to start the liveness detection system.")
    else:
        print("\nSome tests failed. Please check the output above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
