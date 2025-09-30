"""
Camera Service - Wrapper for camera functionality
"""

import cv2
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CameraService:
    """Service for managing camera operations"""
    
    def __init__(self):
        self.camera = None
        self.camera_source = 0
    
    def get_camera(self, source: int = 0) -> Optional[cv2.VideoCapture]:
        """Get camera instance"""
        try:
            if self.camera is None or not self.camera.isOpened():
                self.camera = cv2.VideoCapture(source, cv2.CAP_DSHOW)
                self.camera_source = source
                
                if not self.camera.isOpened():
                    logger.error("Failed to open camera")
                    return None
                
                logger.info(f"Camera opened successfully (source: {source})")
            
            return self.camera
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return None
    
    def is_camera_available(self) -> bool:
        """Check if camera is available"""
        try:
            test_camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if test_camera.isOpened():
                test_camera.release()
                return True
            return False
        except:
            return False
    
    def release_camera(self):
        """Release camera resources"""
        try:
            if self.camera is not None:
                self.camera.release()
                self.camera = None
                logger.info("Camera released")
        except Exception as e:
            logger.error(f"Error releasing camera: {e}")
    
    def get_frame(self) -> Optional[object]:
        """Get frame from camera"""
        try:
            if self.camera is None:
                return None
            
            ret, frame = self.camera.read()
            if not ret:
                logger.warning("Failed to read frame from camera")
                return None
            
            return frame
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            return None
