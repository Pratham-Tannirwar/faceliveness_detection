"""
Person Verification Service - Wrapper for person verification functionality
"""

import cv2
import numpy as np
import logging
import os
import sys
from typing import Dict, Any, Optional

# Add the flask-api directory to the path to import existing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
flask_api_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, flask_api_dir)

logger = logging.getLogger(__name__)

class PersonVerificationService:
    """Service for person verification using InsightFace"""
    
    def __init__(self):
        self.model_loaded = False
        self.face_app = None
        self._load_model()
    
    def _load_model(self):
        """Load InsightFace model"""
        try:
            import insightface
            MODEL_NAME = "buffalo_l"
            self.face_app = insightface.app.FaceAnalysis(
                name=MODEL_NAME, 
                providers=['CPUExecutionProvider']
            )
            self.face_app.prepare(ctx_id=0, det_size=(640, 640))
            self.model_loaded = True
            logger.info("InsightFace model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load InsightFace model: {e}")
            self.model_loaded = False
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model_loaded
    
    def verify_person(self, camera, reference_image: np.ndarray, duration: int = 2, display: bool = False) -> Dict[str, Any]:
        """
        Verify if the person in camera matches the reference image
        
        Args:
            camera: Camera object with get_frame() method
            reference_image: Reference image as numpy array
            duration: Duration to run verification in seconds
            display: Whether to show visual feedback
            
        Returns:
            Dict containing verification results
        """
        if not self.model_loaded:
            return {
                'success': False,
                'confidence': 0.0,
                'message': 'InsightFace model not loaded',
                'error': 'Model not available'
            }
        
        try:
            # Get reference embedding
            ref_faces = self.face_app.get(reference_image)
            if len(ref_faces) != 1:
                return {
                    'success': False,
                    'confidence': 0.0,
                    'message': 'Reference image must contain exactly one face',
                    'error': 'Invalid reference image'
                }
            
            ref_emb = ref_faces[0].embedding / np.linalg.norm(ref_faces[0].embedding)
            
            # Run verification for specified duration
            import time
            start_time = time.time()
            verified = False
            confidence_scores = []
            frame_count = 0
            
            while time.time() - start_time < duration:
                frame = camera.get_frame()
                if frame is None:
                    continue
                
                frame_count += 1
                frame_out = frame.copy()
                
                # Get faces from current frame
                faces = self.face_app.get(frame)
                
                if len(faces) == 0:
                    cv2.putText(frame_out, "❌ No face detected", (30, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                elif len(faces) > 1:
                    cv2.putText(frame_out, "❌ Multiple faces detected", (30, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                else:
                    # Compare with reference
                    test_emb = faces[0].embedding / np.linalg.norm(faces[0].embedding)
                    similarity = np.dot(ref_emb, test_emb)
                    confidence_scores.append(similarity)
                    
                    if similarity > 0.5:  # Threshold for same person
                        verified = True
                        cv2.putText(frame_out, f"✅ Same person (Score: {similarity:.3f})", (30, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame_out, f"❌ Different person (Score: {similarity:.3f})", (30, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                
                if display:
                    cv2.imshow("Person Verification", frame_out)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            
            if display:
                cv2.destroyAllWindows()
            
            # Calculate final confidence
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
            
            return {
                'success': verified,
                'confidence': float(avg_confidence),
                'message': 'Person verification completed',
                'frames_processed': frame_count,
                'confidence_scores': confidence_scores
            }
            
        except Exception as e:
            logger.error(f"Person verification failed: {e}")
            return {
                'success': False,
                'confidence': 0.0,
                'message': f'Person verification failed: {str(e)}',
                'error': str(e)
            }
