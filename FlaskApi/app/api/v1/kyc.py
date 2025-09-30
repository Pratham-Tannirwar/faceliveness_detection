"""
KYC (Know Your Customer) API endpoints
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import KYCSubmission, User
from app.services.kyc_service import KYCService

kyc_ns = Namespace('kyc', description='KYC operations')

@kyc_ns.route('/test')
class KYCTest(Resource):
    def get(self):
        """Test endpoint that doesn't require authentication"""
        return {'message': 'KYC API is working'}, 200

@kyc_ns.route('/debug_test')
class KYCDebugTest(Resource):
    def post(self):
        """Debug test endpoint"""
        try:
            return {
                'success': True,
                'message': 'Debug test endpoint working',
                'data': {'test': 'value'}
            }, 200
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

@kyc_ns.route('/liveness-test')
class LivenessTest(Resource):
    def post(self):
        """Test endpoint for liveness check without authentication"""
        try:
            data = request.get_json()
            image_base64 = data.get('image_base64')
            user_id = data.get('user_id')
            
            if not image_base64:
                return {'success': False, 'message': 'No image provided'}, 400
                
            # Create a simple response for testing
            return {
                'success': True,
                'liveness_result': 'live',
                'confidence': 0.95,
                'message': 'Liveness check successful'
            }, 200
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

@kyc_ns.route('/start_kyc-test')
class StartKYCTest(Resource):
    def post(self):
        """Test endpoint for starting KYC process without authentication"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            
            if not user_id:
                return {'success': False, 'message': 'No user ID provided'}, 400
                
            # Create a simple response for testing
            return {
                'success': True,
                'session_id': 123,
                'message': 'KYC session created successfully'
            }, 200
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

@kyc_ns.route('/voice-captcha-test')
class VoiceCaptchaTest(Resource):
    def post(self):
        """Test endpoint for voice captcha without authentication"""
        try:
            data = request.get_json()
            duration = data.get('duration', 6)
            enable_display = data.get('enable_display', False)
            
            # Create a simple response for testing
            return {
                'success': True,
                'captcha': '45 + 7',
                'expected_answer': '52',
                'message': 'Voice captcha generated successfully'
            }, 200
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

@kyc_ns.route('/voice-captcha-upload')
class VoiceCaptchaUploadTest(Resource):
    def post(self):
        """Test endpoint for voice captcha upload without authentication"""
        try:
            # In a real implementation, we would process the audio file
            # and verify the spoken answer against the expected answer
            
            # Create a simple response for testing
            return {
                'success': True,
                'liveness': True,
                'confidence': 0.95,
                'message': 'Voice verification successful'
            }, 200
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

@kyc_ns.route('/complete-test')
class CompleteTest(Resource):
    def post(self):
        """Test endpoint for complete liveness flow without authentication"""
        try:
            # Parse request data
            data = request.get_json()
            reference_image = data.get('reference_image')
            enable_display = data.get('enable_display', False)
            
            # Create a simple response for testing
            return {
                'success': True,
                'verification_result': 'verified',
                'confidence': 0.98,
                'message': 'Liveness verification completed successfully'
            }, 200
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

# Request/Response models
kyc_submission_model = kyc_ns.model('KYCSubmission', {
    'id': fields.Integer(description='Submission ID'),
    'user_id': fields.Integer(description='User ID'),
    'liveness_result': fields.String(description='Liveness detection result'),
    'status': fields.String(description='KYC status'),
    'submitted_at': fields.String(description='Submission date'),
    'reviewed_at': fields.String(description='Review date'),
    'notes': fields.String(description='Review notes')
})

submit_kyc_model = kyc_ns.model('SubmitKYC', {
    'session_id': fields.Integer(required=True, description='Session ID'),
    'document_images': fields.List(fields.String, description='Base64 encoded document images'),
    'selfie_image': fields.String(required=True, description='Base64 encoded selfie image')
})

@kyc_ns.route('/status')
class KYCStatus(Resource):
    @jwt_required()
    @kyc_ns.marshal_with(kyc_submission_model)
    def get(self):
        """Get current user's KYC status"""
        try:
            current_user_id = get_jwt_identity()
            
            kyc_submission = KYCSubmission.query.filter_by(user_id=current_user_id).order_by(KYCSubmission.submitted_at.desc()).first()
            
            if not kyc_submission:
                return {'message': 'No KYC submission found'}, 404
            
            return kyc_submission.to_dict(), 200
            
        except Exception as e:
            return {'message': f'Failed to get KYC status: {str(e)}'}, 500

@kyc_ns.route('/submit')
class SubmitKYC(Resource):
    @jwt_required()
    @kyc_ns.expect(submit_kyc_model)
    @kyc_ns.marshal_with(kyc_submission_model)
    def post(self):
        """Submit KYC documents for verification"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            session_id = data.get('session_id')
            document_images = data.get('document_images', [])
            selfie_image = data.get('selfie_image')
            
            if not session_id or not selfie_image:
                return {'message': 'Session ID and selfie image are required'}, 400
            
            kyc_service = KYCService()
            result = kyc_service.submit_kyc(current_user_id, session_id, document_images, selfie_image)
            
            if result['success']:
                return result['data'], 201
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'KYC submission failed: {str(e)}'}, 500

@kyc_ns.route('/liveness-check')
class LivenessCheck(Resource):
    @jwt_required()
    def post(self):
        """Perform liveness check for KYC"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            session_id = data.get('session_id')
            image_data = data.get('image_data')
            
            if not session_id or not image_data:
                return {'message': 'Session ID and image data are required'}, 400
            
            kyc_service = KYCService()
            result = kyc_service.perform_liveness_check(current_user_id, session_id, image_data)
            
            if result['success']:
                return result['data'], 200
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Liveness check failed: {str(e)}'}, 500
                
@kyc_ns.route('/start_kyc')
class StartKYC(Resource):
    # @jwt_required()
    def post(self):
        """Start the KYC verification process"""
        try:
            # current_user_id = get_jwt_identity()
            data = request.get_json()
            
            user_id = data.get('user_id')
            
            # Convert string user ID to integer for database operations
            current_user_id_int = int(user_id)
            
            # Validate user_id if provided
            # if user_id and str(user_id) != str(current_user_id):
            #     return {'success': False, 'message': 'Unauthorized access'}, 403
            
            # Create a new KYC session
            kyc_service = KYCService()
            session = kyc_service.create_kyc_session(current_user_id_int)
            print(session)
            
            return {
                'success': True,
                'message': 'KYC verification process started successfully',
                'session_id': session.id if session else None
            }, 200
                
        except Exception as e:
            return {'success': False, 'message': f'Failed to start KYC process: {str(e)}'}, 500

@kyc_ns.route('/start_kyc_simple')
class StartKYCSimple(Resource):
    def post(self):
        """Simple test endpoint for KYC"""
        try:
            return {
                'success': True,
                'message': 'Simple KYC endpoint working',
                'session_id': 999
            }, 200
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

@kyc_ns.route('/history')
class KYCHistory(Resource):
    @jwt_required()
    @kyc_ns.marshal_list_with(kyc_submission_model)
    def get(self):
        """Get user's KYC submission history"""
        try:
            current_user_id = get_jwt_identity()
            
            kyc_submissions = KYCSubmission.query.filter_by(user_id=current_user_id).order_by(KYCSubmission.submitted_at.desc()).all()
            
            return [submission.to_dict() for submission in kyc_submissions], 200
            
        except Exception as e:
            return {'message': f'Failed to get KYC history: {str(e)}'}, 500

@kyc_ns.route('/requirements')
class KYCRequirements(Resource):
    def get(self):
        """Get KYC requirements and guidelines"""
        try:
            requirements = {
                'documents': {
                    'required': ['Government issued ID', 'Proof of address'],
                    'optional': ['Additional identity verification'],
                    'formats': ['JPG', 'PNG', 'PDF'],
                    'max_size': '5MB per document'
                },
                'selfie': {
                    'requirements': ['Clear face visibility', 'Good lighting', 'No accessories covering face'],
                    'formats': ['JPG', 'PNG'],
                    'max_size': '5MB'
                },
                'liveness_check': {
                    'instructions': ['Look directly at camera', 'Blink when prompted', 'Turn head as instructed'],
                    'duration': '30-60 seconds'
                }
            }
            
            return requirements, 200
            
        except Exception as e:
            return {'message': f'Failed to get requirements: {str(e)}'}, 500
