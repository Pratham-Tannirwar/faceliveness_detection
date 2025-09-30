"""
Face detection service
"""

import base64
import json
import cv2
import numpy as np
from datetime import datetime
from app.models import FaceDetection, Session
from app import db

class FaceDetectionService:
    """Service for handling face detection operations"""
    
    def __init__(self):
        # Initialize face detection models
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def decode_image(self, image_data):
        """Decode base64 image data"""
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return image
        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")
    
    def detect_faces(self, image):
        """Detect faces in image using OpenCV"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            face_data = []
            for (x, y, w, h) in faces:
                face_info = {
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'confidence': 0.8  # Default confidence for Haar cascade
                }
                face_data.append(face_info)
            
            return face_data
            
        except Exception as e:
            raise ValueError(f"Face detection failed: {str(e)}")
    
    def calculate_confidence_score(self, face_data):
        """Calculate overall confidence score"""
        if not face_data:
            return 0.0
        
        confidences = [face['confidence'] for face in face_data]
        return sum(confidences) / len(confidences)
    
    def detect_face(self, session_id, user_id, image_data, detection_type='general'):
        """Perform face detection on uploaded image"""
        try:
            # Verify session exists and belongs to user
            session = Session.query.filter_by(id=session_id, user_id=user_id).first()
            if not session:
                return {'success': False, 'message': 'Session not found or access denied'}
            
            # Decode image
            image = self.decode_image(image_data)
            
            # Detect faces
            face_data = self.detect_faces(image)
            
            # Calculate confidence score
            confidence_score = self.calculate_confidence_score(face_data)
            
            # Create face detection record
            detection = FaceDetection(
                session_id=session_id,
                user_id=user_id,
                face_data=face_data,
                confidence_score=confidence_score
            )
            
            db.session.add(detection)
            db.session.commit()
            
            return {
                'success': True,
                'data': detection.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Face detection failed: {str(e)}'}
    
    def liveness_check(self, session_id, user_id, image_data):
        """Perform liveness detection"""
        try:
            # Verify session exists and belongs to user
            session = Session.query.filter_by(id=session_id, user_id=user_id).first()
            if not session:
                return {'success': False, 'message': 'Session not found or access denied'}
            
            # Decode image
            image = self.decode_image(image_data)
            
            # Detect faces
            face_data = self.detect_faces(image)
            
            if not face_data:
                return {'success': False, 'message': 'No face detected in image'}
            
            # Simple liveness check (in a real application, you'd use more sophisticated methods)
            liveness_result = self.perform_simple_liveness_check(image, face_data[0])
            
            # Create face detection record with liveness info
            detection_data = {
                'faces': face_data,
                'liveness_check': liveness_result,
                'detection_type': 'liveness'
            }
            
            detection = FaceDetection(
                session_id=session_id,
                user_id=user_id,
                face_data=detection_data,
                confidence_score=liveness_result['confidence']
            )
            
            db.session.add(detection)
            db.session.commit()
            
            return {
                'success': True,
                'data': {
                    'detection': detection.to_dict(),
                    'liveness_result': liveness_result
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Liveness check failed: {str(e)}'}
    
    def perform_simple_liveness_check(self, image, face_rect):
        """Perform a simple liveness check"""
        try:
            x, y, w, h = face_rect['x'], face_rect['y'], face_rect['width'], face_rect['height']
            
            # Extract face region
            face_region = image[y:y+h, x:x+w]
            
            # Convert to grayscale
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Simple checks for liveness
            # 1. Check for eye regions (simplified)
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(gray_face, scaleFactor=1.1, minNeighbors=3)
            
            # 2. Check image quality (blur detection)
            blur_score = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            
            # 3. Check brightness
            brightness = np.mean(gray_face)
            
            # Determine liveness result
            has_eyes = len(eyes) >= 2
            is_clear = blur_score > 100  # Threshold for clear image
            is_bright_enough = 50 < brightness < 200  # Reasonable brightness range
            
            liveness_score = 0.0
            if has_eyes:
                liveness_score += 0.4
            if is_clear:
                liveness_score += 0.3
            if is_bright_enough:
                liveness_score += 0.3
            
            result = {
                'is_live': liveness_score > 0.6,
                'confidence': liveness_score,
                'checks': {
                    'has_eyes': has_eyes,
                    'is_clear': is_clear,
                    'is_bright_enough': is_bright_enough
                },
                'metrics': {
                    'blur_score': float(blur_score),
                    'brightness': float(brightness),
                    'eyes_detected': len(eyes)
                }
            }
            
            return result
            
        except Exception as e:
            return {
                'is_live': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def get_session_stats(self, session_id):
        """Get face detection statistics for a session"""
        try:
            detections = FaceDetection.query.filter_by(session_id=session_id).all()
            
            if not detections:
                return {
                    'success': True,
                    'data': {
                        'total_detections': 0,
                        'average_confidence': 0.0,
                        'face_count_distribution': {},
                        'detection_timeline': []
                    }
                }
            
            # Calculate statistics
            total_detections = len(detections)
            confidences = [d.confidence_score for d in detections if d.confidence_score]
            average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Face count distribution
            face_counts = {}
            for detection in detections:
                if detection.face_data and isinstance(detection.face_data, list):
                    face_count = len(detection.face_data)
                    face_counts[face_count] = face_counts.get(face_count, 0) + 1
            
            # Detection timeline
            timeline = []
            for detection in detections:
                timeline.append({
                    'timestamp': detection.timestamp.isoformat() if detection.timestamp else None,
                    'confidence': float(detection.confidence_score) if detection.confidence_score else 0.0,
                    'face_count': len(detection.face_data) if detection.face_data else 0
                })
            
            return {
                'success': True,
                'data': {
                    'total_detections': total_detections,
                    'average_confidence': float(average_confidence),
                    'face_count_distribution': face_counts,
                    'detection_timeline': timeline
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to get stats: {str(e)}'}
