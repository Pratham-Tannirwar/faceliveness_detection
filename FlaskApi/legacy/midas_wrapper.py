#!/usr/bin/env python3
"""
MiDaS wrapper for liveness detection integration
Provides a simple interface for the 2D/3D liveness check
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_2d_3d_liveness_check(camera, duration=5, display=True):
    """
    Run 2D/3D liveness check using MiDaS depth estimation and head pose analysis
    
    Args:
        camera: Camera object with get_frame() method
        duration: Duration of the check in seconds (default: 5)
        display: Whether to show visual feedback (default: True)
    
    Returns:
        bool: True if 2D/3D liveness detected, False otherwise
    """
    try:
        # Import the midas liveness module
        from midas_liveness import run_liveness_check_5s
        
        # Temporarily override the camera capture to use our camera object
        import cv2
        
        # Create a mock camera capture that uses our camera object
        class MockCapture:
            def __init__(self, camera_obj):
                self.camera = camera_obj
                self.frame_count = 0
                
            def read(self):
                try:
                    frame = self.camera.get_frame()
                    self.frame_count += 1
                    return True, frame
                except Exception as e:
                    print(f"Error getting frame: {e}")
                    return False, None
                    
            def isOpened(self):
                return True
                
            def release(self):
                pass
        
        # Temporarily patch cv2.VideoCapture to use our mock
        original_VideoCapture = cv2.VideoCapture
        mock_capture = MockCapture(camera)
        
        def mock_VideoCapture(*args, **kwargs):
            return mock_capture
            
        cv2.VideoCapture = mock_VideoCapture
        
        # Temporarily disable display if requested
        import midas_liveness as midas_module
        original_show_windows = getattr(midas_module, 'SHOW_WINDOWS', True)
        midas_module.SHOW_WINDOWS = display
        
        # Run the liveness check
        print("Running 2D/3D liveness check...")
        result = midas_module.run_liveness_check_5s()
        
        # Restore original settings
        cv2.VideoCapture = original_VideoCapture
        midas_module.SHOW_WINDOWS = original_show_windows
        
        if result:
            print("2D/3D liveness confirmed!")
        else:
            print("2D/3D analysis detected spoof attempt")
        
        return result
        
    except Exception as e:
        print(f"2D/3D liveness check failed: {e}")
        return False

# Simple test function
def test_2d_3d_check():
    """Test the 2D/3D liveness check functionality"""
    from camera import Camera
    
    print("Testing 2D/3D liveness check...")
    cam = Camera(0)
    
    try:
        result = run_2d_3d_liveness_check(cam, duration=3, display=True)
        print(f"2D/3D check result: {'LIVE' if result else 'SPOOF'}")
        return result
    finally:
        cam.release()

if __name__ == "__main__":
    test_2d_3d_check()