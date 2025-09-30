"""
Comprehensive Liveness Detection Service
Integrates all existing liveness detection modules into a unified service
"""

import cv2
import numpy as np
import base64
import os
import tempfile
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Import existing modules
from .camera_service import CameraService
from .person_verification_service import PersonVerificationService
from .blink_detection_service import BlinkDetectionService
from .mouth_captcha_service import MouthCaptchaService
from .midas_liveness_service import MidasLivenessService

logger = logging.getLogger(__name__)

class LivenessDetectionService:
    """Comprehensive liveness detection service integrating all detection methods"""
    
    def __init__(self):
        self.camera_service = CameraService()
        self.person_verification = PersonVerificationService()
        self.blink_detection = BlinkDetectionService()
        self.mouth_captcha = MouthCaptchaService()
        self.midas_liveness = MidasLivenessService()
        
        # Configuration
        self.config = {
            'person_verification_duration': 2,
            'midas_liveness_duration': 5,
            'blink_detection_duration': 4,
            'mouth_captcha_duration': 7,
            'enable_display': False,  # Disable for API mode
            'confidence_threshold': 0.7
        }
    
    def decode_image_from_base64(self, image_data: str) -> np.ndarray:
        """Decode base64 image data to OpenCV format"""
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Failed to decode image")
            
            return image
        except Exception as e:
            raise ValueError(f"Image decoding failed: {str(e)}")
    
    def encode_image_to_base64(self, image: np.ndarray) -> str:
        """Encode OpenCV image to base64 string"""
        try:
            _, buffer = cv2.imencode('.jpg', image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            return image_base64
        except Exception as e:
            raise ValueError(f"Image encoding failed: {str(e)}")
    
    def run_complete_liveness_detection(self, reference_image_data: Optional[str] = None) -> Dict[str, Any]:
        """
        Run complete liveness detection sequence with all verification steps
        
        Args:
            reference_image_data: Base64 encoded reference image (optional)
            
        Returns:
            Dict containing detection results and confidence scores
        """
        results = {
            'success': False,
            'is_live': False,
            'confidence': 0.0,
            'steps': {},
            'timestamp': datetime.utcnow().isoformat(),
            'error': None
        }
        
        try:
            logger.info("Starting complete liveness detection sequence")
            
            # Initialize camera
            camera = self.camera_service.get_camera()
            if not camera:
                raise RuntimeError("Camera not available")
            
            step_results = {}
            total_confidence = 0.0
            passed_steps = 0
            
            # Step 1: Person Verification (if reference image provided)
            if reference_image_data:
                logger.info("Step 1/4: Person Verification")
                try:
                    reference_image = self.decode_image_from_base64(reference_image_data)
                    person_result = self.person_verification.verify_person(
                        camera, reference_image, 
                        duration=self.config['person_verification_duration'],
                        display=self.config['enable_display']
                    )
                    
                    step_results['person_verification'] = {
                        'passed': person_result['success'],
                        'confidence': person_result['confidence'],
                        'message': person_result['message']
                    }
                    
                    if person_result['success']:
                        passed_steps += 1
                        total_confidence += person_result['confidence']
                        logger.info("✅ Person verification passed")
                    else:
                        logger.warning("❌ Person verification failed")
                        results['error'] = "Person verification failed"
                        return results
                        
                except Exception as e:
                    logger.error(f"Person verification error: {e}")
                    step_results['person_verification'] = {
                        'passed': False,
                        'confidence': 0.0,
                        'error': str(e)
                    }
            else:
                logger.info("Skipping person verification (no reference image)")
                step_results['person_verification'] = {
                    'passed': True,
                    'confidence': 1.0,
                    'message': 'Skipped - no reference image provided'
                }
                passed_steps += 1
                total_confidence += 1.0
            
            # Step 2: 2D/3D Liveness Check using MiDaS
            logger.info("Step 2/4: 2D/3D Liveness Check")
            try:
                midas_result = self.midas_liveness.run_liveness_check(
                    camera,
                    duration=self.config['midas_liveness_duration'],
                    display=self.config['enable_display']
                )
                
                step_results['midas_liveness'] = {
                    'passed': midas_result['success'],
                    'confidence': midas_result['confidence'],
                    'message': midas_result['message']
                }
                
                if midas_result['success']:
                    passed_steps += 1
                    total_confidence += midas_result['confidence']
                    logger.info("✅ 2D/3D liveness check passed")
                else:
                    logger.warning("❌ 2D/3D liveness check failed")
                    results['error'] = "2D/3D liveness check failed"
                    return results
                    
            except Exception as e:
                logger.error(f"MiDaS liveness check error: {e}")
                step_results['midas_liveness'] = {
                    'passed': False,
                    'confidence': 0.0,
                    'error': str(e)
                }
            
            # Step 3: Blink Detection
            logger.info("Step 3/4: Blink Detection")
            try:
                blink_result = self.blink_detection.detect_blinks(
                    camera,
                    duration=self.config['blink_detection_duration'],
                    display=self.config['enable_display']
                )
                
                step_results['blink_detection'] = {
                    'passed': blink_result['success'],
                    'confidence': blink_result['confidence'],
                    'blinks_detected': blink_result.get('blinks_detected', 0),
                    'gaze_movements': blink_result.get('gaze_movements', 0),
                    'message': blink_result['message']
                }
                
                if blink_result['success']:
                    passed_steps += 1
                    total_confidence += blink_result['confidence']
                    logger.info("✅ Blink detection passed")
                else:
                    logger.warning("❌ Blink detection failed")
                    results['error'] = "Blink detection failed"
                    return results
                    
            except Exception as e:
                logger.error(f"Blink detection error: {e}")
                step_results['blink_detection'] = {
                    'passed': False,
                    'confidence': 0.0,
                    'error': str(e)
                }
            
            # Step 4: Voice Captcha Verification
            logger.info("Step 4/4: Voice Captcha Verification")
            try:
                captcha_result = self.mouth_captcha.run_captcha_verification(
                    camera,
                    duration=self.config['mouth_captcha_duration'],
                    display=self.config['enable_display']
                )
                
                step_results['mouth_captcha'] = {
                    'passed': captcha_result['success'],
                    'confidence': captcha_result['confidence'],
                    'captcha_question': captcha_result.get('question', ''),
                    'captcha_answer': captcha_result.get('answer', ''),
                    'spoken_text': captcha_result.get('spoken_text', ''),
                    'message': captcha_result['message']
                }
                
                if captcha_result['success']:
                    passed_steps += 1
                    total_confidence += captcha_result['confidence']
                    logger.info("✅ Voice captcha verification passed")
                else:
                    logger.warning("❌ Voice captcha verification failed")
                    results['error'] = "Voice captcha verification failed"
                    return results
                    
            except Exception as e:
                logger.error(f"Voice captcha error: {e}")
                step_results['mouth_captcha'] = {
                    'passed': False,
                    'confidence': 0.0,
                    'error': str(e)
                }
            
            # Calculate final results
            final_confidence = total_confidence / passed_steps if passed_steps > 0 else 0.0
            is_live = passed_steps >= 3 and final_confidence >= self.config['confidence_threshold']
            
            results.update({
                'success': True,
                'is_live': is_live,
                'confidence': final_confidence,
                'steps': step_results,
                'passed_steps': passed_steps,
                'total_steps': 4,
                'message': 'Liveness detection completed successfully' if is_live else 'Liveness detection failed'
            })
            
            if is_live:
                logger.info("🎉 SUCCESS: Person is LIVE! All verification steps passed.")
            else:
                logger.warning("❌ VERIFICATION FAILED: Spoof attempt detected")
            
            return results
            
        except Exception as e:
            logger.error(f"Liveness detection failed: {e}")
            results['error'] = str(e)
            return results
        
        finally:
            # Clean up camera
            try:
                self.camera_service.release_camera()
            except:
                pass
    
    def run_individual_step(self, step_name: str, image_data: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Run individual liveness detection step
        
        Args:
            step_name: Name of the step to run
            image_data: Base64 encoded image data (for person verification)
            **kwargs: Additional parameters for the specific step
            
        Returns:
            Dict containing step results
        """
        try:
            camera = self.camera_service.get_camera()
            if not camera:
                raise RuntimeError("Camera not available")
            
            if step_name == 'person_verification':
                if not image_data:
                    raise ValueError("Reference image required for person verification")
                reference_image = self.decode_image_from_base64(image_data)
                return self.person_verification.verify_person(
                    camera, reference_image, 
                    duration=kwargs.get('duration', self.config['person_verification_duration']),
                    display=kwargs.get('display', self.config['enable_display'])
                )
            
            elif step_name == 'midas_liveness':
                return self.midas_liveness.run_liveness_check(
                    camera,
                    duration=kwargs.get('duration', self.config['midas_liveness_duration']),
                    display=kwargs.get('display', self.config['enable_display'])
                )
            
            elif step_name == 'blink_detection':
                return self.blink_detection.detect_blinks(
                    camera,
                    duration=kwargs.get('duration', self.config['blink_detection_duration']),
                    display=kwargs.get('display', self.config['enable_display'])
                )
            
            elif step_name == 'mouth_captcha':
                return self.mouth_captcha.run_captcha_verification(
                    camera,
                    duration=kwargs.get('duration', self.config['mouth_captcha_duration']),
                    display=kwargs.get('display', self.config['enable_display'])
                )
            
            else:
                raise ValueError(f"Unknown step: {step_name}")
                
        except Exception as e:
            logger.error(f"Individual step {step_name} failed: {e}")
            return {
                'success': False,
                'confidence': 0.0,
                'error': str(e),
                'message': f"Step {step_name} failed"
            }
        
        finally:
            try:
                self.camera_service.release_camera()
            except:
                pass
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and available capabilities"""
        return {
            'camera_available': self.camera_service.is_camera_available(),
            'models_loaded': {
                'person_verification': self.person_verification.is_model_loaded(),
                'blink_detection': self.blink_detection.is_model_loaded(),
                'mouth_captcha': self.mouth_captcha.is_model_loaded(),
                'midas_liveness': self.midas_liveness.is_model_loaded()
            },
            'configuration': self.config,
            'timestamp': datetime.utcnow().isoformat()
        }
