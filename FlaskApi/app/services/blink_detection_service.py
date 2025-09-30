"""
Blink Detection Service - Wrapper for blink detection functionality
"""

import cv2
import numpy as np
import logging
import os
import sys
import time
from typing import Dict, Any

# Add the flask-api directory to the path to import existing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
flask_api_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, flask_api_dir)

logger = logging.getLogger(__name__)

class BlinkDetectionService:
    """Service for blink and gaze movement detection"""
    
    def __init__(self):
        self.model_loaded = False
        self.detector = None
        self.predictor = None
        self._load_model()
    
    def _load_model(self):
        """Load dlib models for facial landmark detection"""
        try:
            import dlib
            import bz2
            import urllib.request
            from imutils import face_utils
            from scipy.spatial import distance as dist
            
            # Download predictor if missing
            predictor_path = os.path.join(flask_api_dir, "shape_predictor_68_face_landmarks.dat")
            if not os.path.exists(predictor_path):
                logger.info("Downloading facial landmark predictor...")
                url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
                urllib.request.urlretrieve(url, "sp.dat.bz2")
                with bz2.open("sp.dat.bz2") as f_in, open(predictor_path, "wb") as f_out:
                    f_out.write(f_in.read())
                os.remove("sp.dat.bz2")
                logger.info("Facial landmark predictor downloaded")
            
            # Load models
            self.detector = dlib.get_frontal_face_detector()
            self.predictor = dlib.shape_predictor(predictor_path)
            self.face_utils = face_utils
            self.dist = dist
            
            # Eye landmark indices
            (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
            (self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
            
            self.model_loaded = True
            logger.info("Blink detection models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load blink detection models: {e}")
            self.model_loaded = False
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model_loaded
    
    def eye_aspect_ratio(self, eye):
        """Compute Eye Aspect Ratio for one eye"""
        A = self.dist.euclidean(eye[1], eye[5])
        B = self.dist.euclidean(eye[2], eye[4])
        C = self.dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)
    
    def get_gaze_ratio(self, eye_points, facial_landmarks, gray):
        """Compute gaze ratio (left/right)"""
        eye_region = np.array([(facial_landmarks.part(point).x, facial_landmarks.part(point).y)
                               for point in eye_points])
        min_x = np.min(eye_region[:, 0])
        max_x = np.max(eye_region[:, 0])
        min_y = np.min(eye_region[:, 1])
        max_y = np.max(eye_region[:, 1])

        gray_eye = gray[min_y:max_y, min_x:max_x]
        _, threshold_eye = cv2.threshold(gray_eye, 70, 255, cv2.THRESH_BINARY)

        height, width = threshold_eye.shape
        left_side = threshold_eye[:, 0:int(width / 2)]
        right_side = threshold_eye[:, int(width / 2):width]

        left_white = cv2.countNonZero(left_side)
        right_white = cv2.countNonZero(right_side)

        if right_white == 0:
            gaze_ratio = 1
        elif left_white == 0:
            gaze_ratio = 5
        else:
            gaze_ratio = left_white / right_white
        return gaze_ratio
    
    def detect_blinks(self, camera, duration: int = 4, display: bool = False) -> Dict[str, Any]:
        """
        Detect natural blinks and gaze movements for liveness
        
        Args:
            camera: Camera object with get_frame() method
            duration: Duration to run detection in seconds
            display: Whether to show visual feedback
            
        Returns:
            Dict containing detection results
        """
        if not self.model_loaded:
            return {
                'success': False,
                'confidence': 0.0,
                'message': 'Blink detection models not loaded',
                'error': 'Models not available'
            }
        
        try:
            # Thresholds
            EYE_AR_THRESH = 0.22
            EYE_AR_CONSEC_FRAMES = 2
            
            counter = 0
            total_blinks = 0
            gaze_movements = 0
            ear_values = []
            gaze_values = []
            
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < duration:
                frame = camera.get_frame()
                if frame is None:
                    continue
                
                frame_count += 1
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                rects = self.detector(gray, 0)

                for rect in rects:
                    shape = self.predictor(gray, rect)
                    shape_np = self.face_utils.shape_to_np(shape)

                    left_eye = shape_np[self.lStart:self.lEnd]
                    right_eye = shape_np[self.rStart:self.rEnd]
                    left_ear = self.eye_aspect_ratio(left_eye)
                    right_ear = self.eye_aspect_ratio(right_eye)
                    ear = (left_ear + right_ear) / 2.0
                    ear_values.append(ear)

                    # Blink detection
                    if ear < EYE_AR_THRESH:
                        counter += 1
                    else:
                        if counter >= EYE_AR_CONSEC_FRAMES:
                            total_blinks += 1
                        counter = 0

                    # Draw eyes
                    if display:
                        cv2.drawContours(frame, [cv2.convexHull(left_eye)], -1, (0, 255, 0), 1)
                        cv2.drawContours(frame, [cv2.convexHull(right_eye)], -1, (0, 255, 0), 1)

                    # Gaze movement detection
                    gaze_left = self.get_gaze_ratio([36, 37, 38, 39, 40, 41], shape, gray)
                    gaze_right = self.get_gaze_ratio([42, 43, 44, 45, 46, 47], shape, gray)
                    gaze_avg = (gaze_left + gaze_right) / 2
                    gaze_values.append(gaze_avg)

                    if gaze_avg <= 0.8 or gaze_avg >= 1.5:
                        gaze_movements += 1

                    # Overlay info
                    if display:
                        cv2.putText(frame, f"Blinks: {total_blinks}", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.putText(frame, f"Gaze Movements: {gaze_movements}", (10, 60),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                        cv2.putText(frame, f"EAR: {ear:.2f}", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Display
                if display:
                    cv2.imshow("Blink + Gaze Liveness", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

            if display:
                cv2.destroyAllWindows()
            
            # Calculate confidence based on blinks and gaze movements
            blink_score = min(1.0, total_blinks / 2.0)  # Normalize to 0-1
            gaze_score = min(1.0, gaze_movements / 3.0)  # Normalize to 0-1
            confidence = (blink_score + gaze_score) / 2.0
            
            # Success criteria
            success = total_blinks >= 1 and gaze_movements >= 2
            
            return {
                'success': success,
                'confidence': float(confidence),
                'blinks_detected': total_blinks,
                'gaze_movements': gaze_movements,
                'frames_processed': frame_count,
                'avg_ear': float(np.mean(ear_values)) if ear_values else 0.0,
                'avg_gaze': float(np.mean(gaze_values)) if gaze_values else 0.0,
                'message': 'Blink detection completed successfully' if success else 'Insufficient blink/gaze activity detected'
            }
            
        except Exception as e:
            logger.error(f"Blink detection failed: {e}")
            return {
                'success': False,
                'confidence': 0.0,
                'message': f'Blink detection failed: {str(e)}',
                'error': str(e)
            }
