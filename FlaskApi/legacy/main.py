from person_check import PersonVerificationAndMonitor
from camera import Camera
from blink import blink
from mouth_mov import mouth_captcha_verification
from midas_wrapper import run_2d_3d_liveness_check
import os
import cv2

def run_liveness_detection():
    """Complete liveness detection sequence with 2D/3D check"""
    cam = Camera(0)
    
    try:
        # Use relative paths for better portability
        current_dir = os.path.dirname(os.path.abspath(__file__))
        reference_image_path = os.path.join(current_dir, "reference_images", "princee.jpg")
        
        print("Starting liveness detection sequence...")
        
        # Step 1: Person verification (compare with reference)
        print("\n[Step 1/4] Person Verification - Comparing with reference image...")
        verifier = PersonVerificationAndMonitor(reference_image_path)
        pc_result, frame = verifier.run(cam, duration=2, display=True)
        
        if not pc_result:
            print("Spoof detected - Person verification failed")
            return False
        
        print("Same person detected!")
        
        # Step 2: 2D/3D liveness check using MiDaS
        print("\n[Step 2/4] 2D/3D Liveness Check - Analyzing depth and head pose...")
        midas_result = run_2d_3d_liveness_check(cam, duration=5, display=True)
        
        if not midas_result:
            print("Spoof detected - 2D/3D analysis failed")
            return False
        
        print("2D/3D liveness confirmed!")
        
        # Step 3: Blink detection
        print("\n[Step 3/4] Blink Detection - Checking for natural eye movements...")
        blink_result = blink(cam, duration=4, display=True)
        
        if not blink_result:
            print("Spoof detected - No natural blinking detected")
            return False
        
        print("Natural blinking and gaze movements detected!")
        
        # Step 4: Voice captcha verification
        print("\n[Step 4/4] Voice Captcha - Verifying voice and mouth movements...")
        VOSK_PATH = os.getenv("VOSK_PATH", os.path.join(current_dir, "vosk-model-small-en-us-0.15"))
        DLIB_PATH = os.getenv("DLIB_PATH", os.path.join(current_dir, "shape_predictor_68_face_landmarks.dat"))
        captcha_result = mouth_captcha_verification(cam, VOSK_PATH, DLIB_PATH, duration=7, display=True)
        
        if not captcha_result:
            print("Spoof detected - Voice verification failed")
            return False
        
        print("Voice verification completed!")
        
        print("\n🎉 SUCCESS: Person is LIVE!! All verification steps passed.")
        return True
        
    finally:
        cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    success = run_liveness_detection()
    if not success:
        print("\nVERIFICATION FAILED: Spoof attempt detected")
        exit(1)
    else:
        print("\nVERIFICATION SUCCESSFUL: Live person confirmed")