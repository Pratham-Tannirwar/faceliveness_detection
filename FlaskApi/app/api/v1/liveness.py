"""
Liveness Detection API endpoints
"""

import time
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.liveness_service import LivenessDetectionService
from app.services.mouth_captcha_service import MouthCaptchaService
from app.models import Session
from app import db

liveness_ns = Namespace('liveness', description='Liveness detection operations')

# Request/Response models
complete_liveness_model = liveness_ns.model('CompleteLiveness', {
    'reference_image': fields.String(description='Base64 encoded reference image (optional)'),
    'enable_display': fields.Boolean(description='Enable visual display (default: false)')
})

individual_step_model = liveness_ns.model('IndividualStep', {
    'step_name': fields.String(required=True, description='Step name: person_verification, midas_liveness, blink_detection, mouth_captcha'),
    'reference_image': fields.String(description='Base64 encoded reference image (for person_verification)'),
    'duration': fields.Integer(description='Duration in seconds (optional)'),
    'enable_display': fields.Boolean(description='Enable visual display (default: false)')
})

liveness_result_model = liveness_ns.model('LivenessResult', {
    'success': fields.Boolean(description='Overall success status'),
    'is_live': fields.Boolean(description='Whether person is detected as live'),
    'confidence': fields.Float(description='Overall confidence score'),
    'steps': fields.Raw(description='Individual step results'),
    'passed_steps': fields.Integer(description='Number of steps that passed'),
    'total_steps': fields.Integer(description='Total number of steps'),
    'message': fields.String(description='Result message'),
    'timestamp': fields.String(description='Detection timestamp'),
    'error': fields.String(description='Error message if any')
})

system_status_model = liveness_ns.model('SystemStatus', {
    'camera_available': fields.Boolean(description='Camera availability'),
    'models_loaded': fields.Raw(description='Model loading status'),
    'configuration': fields.Raw(description='System configuration'),
    'timestamp': fields.String(description='Status timestamp')
})

@liveness_ns.route('/complete')
class CompleteLivenessDetection(Resource):
    @jwt_required()
    @liveness_ns.expect(complete_liveness_model)
    @liveness_ns.marshal_with(liveness_result_model)
    def post(self):
        """Run complete liveness detection sequence with all verification steps"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            reference_image = data.get('reference_image')
            enable_display = data.get('enable_display', False)
            
            # Create a session for this liveness check
            session = Session(
                user_id=current_user_id,
                session_name='Complete Liveness Detection',
                room_id=f'liveness_{current_user_id}_{int(time.time())}',
                is_active=True
            )
            db.session.add(session)
            db.session.commit()
            
            # Initialize liveness service
            liveness_service = LivenessDetectionService()
            
            # Configure service
            if enable_display:
                liveness_service.config['enable_display'] = True
            
            # Run complete liveness detection
            result = liveness_service.run_complete_liveness_detection(reference_image)
            
            # Update session with results
            session.is_active = False
            db.session.commit()
            
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            return {
                'success': False,
                'is_live': False,
                'confidence': 0.0,
                'error': f'Liveness detection failed: {str(e)}',
                'message': 'Internal server error'
            }, 500

@liveness_ns.route('/step')
class IndividualLivenessStep(Resource):
    @jwt_required()
    @liveness_ns.expect(individual_step_model)
    def post(self):
        """Run individual liveness detection step"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            step_name = data.get('step_name')
            reference_image = data.get('reference_image')
            duration = data.get('duration')
            enable_display = data.get('enable_display', False)
            
            if not step_name:
                return {'error': 'step_name is required'}, 400
            
            valid_steps = ['person_verification', 'midas_liveness', 'blink_detection', 'mouth_captcha']
            if step_name not in valid_steps:
                return {'error': f'Invalid step_name. Must be one of: {valid_steps}'}, 400
            
            # Create a session for this step
            session = Session(
                user_id=current_user_id,
                session_name=f'{step_name.replace("_", " ").title()} Detection',
                room_id=f'{step_name}_{current_user_id}_{int(time.time())}',
                is_active=True
            )
            db.session.add(session)
            db.session.commit()
            
            # Initialize liveness service
            liveness_service = LivenessDetectionService()
            
            # Run individual step
            result = liveness_service.run_individual_step(
                step_name=step_name,
                image_data=reference_image,
                duration=duration,
                display=enable_display
            )
            
            # Update session with results
            session.is_active = False
            db.session.commit()
            
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            return {
                'success': False,
                'confidence': 0.0,
                'error': f'Step execution failed: {str(e)}',
                'message': 'Internal server error'
            }, 500

@liveness_ns.route('/person-verification')
class PersonVerification(Resource):
    @jwt_required()
    def post(self):
        """Run person verification against reference image"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            reference_image = data.get('reference_image')
            if not reference_image:
                return {'error': 'reference_image is required'}, 400
            
            # Create a session for this verification
            session = Session(
                user_id=current_user_id,
                session_name='Person Verification',
                room_id=f'person_verification_{current_user_id}_{int(time.time())}',
                is_active=True
            )
            db.session.add(session)
            db.session.commit()
            
            # Initialize liveness service
            liveness_service = LivenessDetectionService()
            
            # Run person verification
            result = liveness_service.run_individual_step(
                step_name='person_verification',
                image_data=reference_image,
                display=data.get('enable_display', False)
            )
            
            # Update session with results
            session.is_active = False
            db.session.commit()
            
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            return {
                'success': False,
                'confidence': 0.0,
                'error': f'Person verification failed: {str(e)}',
                'message': 'Internal server error'
            }, 500

@liveness_ns.route('/2d-3d-check')
class Liveness2D3DCheck(Resource):
    @jwt_required()
    def post(self):
        """Run 2D/3D liveness check using MiDaS depth estimation"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            # Create a session for this check
            session = Session(
                user_id=current_user_id,
                session_name='2D/3D Liveness Check',
                room_id=f'2d3d_check_{current_user_id}_{int(time.time())}',
                is_active=True
            )
            db.session.add(session)
            db.session.commit()
            
            # Initialize liveness service
            liveness_service = LivenessDetectionService()
            
            # Run 2D/3D check
            result = liveness_service.run_individual_step(
                step_name='midas_liveness',
                duration=data.get('duration'),
                display=data.get('enable_display', False)
            )
            
            # Update session with results
            session.is_active = False
            db.session.commit()
            
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            return {
                'success': False,
                'confidence': 0.0,
                'error': f'2D/3D liveness check failed: {str(e)}',
                'message': 'Internal server error'
            }, 500

@liveness_ns.route('/blink-detection')
class BlinkDetection(Resource):
    @jwt_required()
    def post(self):
        """Run blink and gaze movement detection"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            # Create a session for this detection
            session = Session(
                user_id=current_user_id,
                session_name='Blink Detection',
                room_id=f'blink_detection_{current_user_id}_{int(time.time())}',
                is_active=True
            )
            db.session.add(session)
            db.session.commit()
            
            # Initialize liveness service
            liveness_service = LivenessDetectionService()
            
            # Run blink detection
            result = liveness_service.run_individual_step(
                step_name='blink_detection',
                duration=data.get('duration'),
                display=data.get('enable_display', False)
            )
            
            # Update session with results
            session.is_active = False
            db.session.commit()
            
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            return {
                'success': False,
                'confidence': 0.0,
                'error': f'Blink detection failed: {str(e)}',
                'message': 'Internal server error'
            }, 500

@liveness_ns.route('/voice-captcha')
class VoiceCaptcha(Resource):
    @jwt_required()
    def post(self):
        """Run voice captcha verification with mouth movement detection"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json() or {}
            
            # Create a session for this verification
            session = Session(
                user_id=current_user_id,
                session_name='Voice Captcha Verification',
                room_id=f'voice_captcha_{current_user_id}_{int(time.time())}',
                is_active=True
            )
            db.session.add(session)
            db.session.commit()
            
            # Initialize liveness service
            liveness_service = LivenessDetectionService()
            
            # Run voice captcha
            result = liveness_service.run_individual_step(
                step_name='mouth_captcha',
                duration=data.get('duration'),
                display=data.get('enable_display', False)
            )
            
            # Update session with results
            session.is_active = False
            db.session.commit()
            
            # Unify response shape
            return {
                'liveness': bool(result.get('success')),
                'message': result.get('message', 'OK')
            }, 200 if result.get('success') else 400
            
        except Exception as e:
            return {
                'success': False,
                'confidence': 0.0,
                'error': f'Voice captcha verification failed: {str(e)}',
                'message': 'Internal server error'
            }, 500

@liveness_ns.route('/voice-captcha-public')
class VoiceCaptchaPublic(Resource):
    @jwt_required()
    def post(self):
        """Run voice captcha verification without authentication (for demo/testing)"""
        try:
            data = request.get_json() or {}
            duration = data.get('duration')
            enable_display = data.get('enable_display', False)

            # Initialize liveness service
            liveness_service = LivenessDetectionService()

            # Run voice captcha
            result = liveness_service.run_individual_step(
                step_name='mouth_captcha',
                duration=duration,
                display=enable_display
            )
            return {
                'liveness': bool(result.get('success')),
                'message': result.get('message', 'OK')
            }, 200 if result.get('success') else 400

        except Exception as e:
            return {
                'success': False,
                'confidence': 0.0,
                'error': f'Voice captcha (public) failed: {str(e)}',
                'message': 'Internal server error'
            }, 500

upload_model = liveness_ns.model('VoiceCaptchaUpload', {
    'expression': fields.String(description='Math expression shown to user, e.g., "23 + 4"')
})

@liveness_ns.route('/voice-captcha-upload')
class VoiceCaptchaUpload(Resource):
    @jwt_required()
    @liveness_ns.expect(upload_model)
    def post(self):
        """Verify uploaded audio against mouth captcha and spoken answer"""
        try:
            # Expect multipart/form-data with 'audio' file, and optional JSON field 'expression'
            if 'audio' not in request.files:
                return {'success': False, 'message': 'audio file is required'}, 400

            audio_file = request.files['audio']
            expression = request.form.get('expression') or request.json.get('expression') if request.is_json else request.form.get('expression')

            # Read audio bytes
            audio_bytes = audio_file.read()

            # Run verification using service
            service = MouthCaptchaService()
            result = service.verify_uploaded_audio(audio_bytes=audio_bytes, expression=expression)
            return {
                'liveness': bool(result.get('success')),
                'message': result.get('message', 'OK')
            }, 200 if result.get('success') else 400

        except Exception as e:
            return {
                'success': False,
                'confidence': 0.0,
                'error': f'Voice captcha upload failed: {str(e)}',
                'message': 'Internal server error'
            }, 500

@liveness_ns.route('/status')
class LivenessSystemStatus(Resource):
    @liveness_ns.marshal_with(system_status_model)
    def get(self):
        """Get liveness detection system status and capabilities"""
        try:
            liveness_service = LivenessDetectionService()
            status = liveness_service.get_system_status()
            return status, 200
        except Exception as e:
            return {
                'camera_available': False,
                'models_loaded': {},
                'configuration': {},
                'error': str(e)
            }, 500

@liveness_ns.route('/test')
class LivenessTest(Resource):
    def get(self):
        """Test liveness detection system components"""
        try:
            liveness_service = LivenessDetectionService()
            status = liveness_service.get_system_status()
            
            test_results = {
                'system_status': status,
                'tests': {
                    'camera_available': status['camera_available'],
                    'models_loaded': all(status['models_loaded'].values()),
                    'configuration_valid': bool(status['configuration'])
                },
                'overall_status': 'READY' if all([
                    status['camera_available'],
                    all(status['models_loaded'].values()),
                    bool(status['configuration'])
                ]) else 'NOT_READY'
            }
            
            return test_results, 200
        except Exception as e:
            return {
                'system_status': {},
                'tests': {},
                'overall_status': 'ERROR',
                'error': str(e)
            }, 500
