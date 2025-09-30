"""
Face Detection API endpoints
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import FaceDetection, Session
from app.services.face_detection_service import FaceDetectionService

face_detection_ns = Namespace('face-detection', description='Face detection operations')

# Request/Response models
face_detection_model = face_detection_ns.model('FaceDetection', {
    'id': fields.Integer(description='Detection ID'),
    'session_id': fields.Integer(description='Session ID'),
    'user_id': fields.Integer(description='User ID'),
    'face_data': fields.Raw(description='Face detection data'),
    'confidence_score': fields.Float(description='Confidence score'),
    'timestamp': fields.String(description='Detection timestamp')
})

detect_face_model = face_detection_ns.model('DetectFace', {
    'session_id': fields.Integer(required=True, description='Session ID'),
    'image_data': fields.String(required=True, description='Base64 encoded image data'),
    'detection_type': fields.String(description='Type of detection (liveness, emotion, etc.)')
})

@face_detection_ns.route('/detect')
class DetectFace(Resource):
    @jwt_required()
    @face_detection_ns.expect(detect_face_model)
    @face_detection_ns.marshal_with(face_detection_model)
    def post(self):
        """Perform face detection on uploaded image"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            session_id = data.get('session_id')
            image_data = data.get('image_data')
            detection_type = data.get('detection_type', 'general')
            
            if not session_id or not image_data:
                return {'message': 'Session ID and image data are required'}, 400
            
            # Verify session belongs to user
            session = Session.query.filter_by(id=session_id, user_id=current_user_id).first()
            if not session:
                return {'message': 'Session not found or access denied'}, 404
            
            face_detection_service = FaceDetectionService()
            result = face_detection_service.detect_face(session_id, current_user_id, image_data, detection_type)
            
            if result['success']:
                return result['data'], 201
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Face detection failed: {str(e)}'}, 500

@face_detection_ns.route('/session/<int:session_id>')
class SessionDetections(Resource):
    @jwt_required()
    @face_detection_ns.marshal_list_with(face_detection_model)
    def get(self, session_id):
        """Get all face detections for a session"""
        try:
            current_user_id = get_jwt_identity()
            
            # Verify session belongs to user
            session = Session.query.filter_by(id=session_id, user_id=current_user_id).first()
            if not session:
                return {'message': 'Session not found or access denied'}, 404
            
            detections = FaceDetection.query.filter_by(session_id=session_id).order_by(FaceDetection.timestamp.desc()).all()
            
            return [detection.to_dict() for detection in detections], 200
            
        except Exception as e:
            return {'message': f'Failed to get detections: {str(e)}'}, 500

@face_detection_ns.route('/<int:detection_id>')
class DetectionById(Resource):
    @jwt_required()
    @face_detection_ns.marshal_with(face_detection_model)
    def get(self, detection_id):
        """Get specific face detection by ID"""
        try:
            current_user_id = get_jwt_identity()
            
            detection = FaceDetection.query.filter_by(id=detection_id, user_id=current_user_id).first()
            
            if not detection:
                return {'message': 'Detection not found'}, 404
            
            return detection.to_dict(), 200
            
        except Exception as e:
            return {'message': f'Failed to get detection: {str(e)}'}, 500

@face_detection_ns.route('/liveness-check')
class LivenessCheck(Resource):
    @jwt_required()
    @face_detection_ns.expect(detect_face_model)
    def post(self):
        """Perform liveness detection for KYC"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            session_id = data.get('session_id')
            image_data = data.get('image_data')
            
            if not session_id or not image_data:
                return {'message': 'Session ID and image data are required'}, 400
            
            # Verify session belongs to user
            session = Session.query.filter_by(id=session_id, user_id=current_user_id).first()
            if not session:
                return {'message': 'Session not found or access denied'}, 404
            
            face_detection_service = FaceDetectionService()
            result = face_detection_service.liveness_check(session_id, current_user_id, image_data)
            
            if result['success']:
                return result['data'], 200
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Liveness check failed: {str(e)}'}, 500

@face_detection_ns.route('/stats/<int:session_id>')
class DetectionStats(Resource):
    @jwt_required()
    def get(self, session_id):
        """Get face detection statistics for a session"""
        try:
            current_user_id = get_jwt_identity()
            
            # Verify session belongs to user
            session = Session.query.filter_by(id=session_id, user_id=current_user_id).first()
            if not session:
                return {'message': 'Session not found or access denied'}, 404
            
            face_detection_service = FaceDetectionService()
            result = face_detection_service.get_session_stats(session_id)
            
            if result['success']:
                return result['data'], 200
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Failed to get stats: {str(e)}'}, 500
