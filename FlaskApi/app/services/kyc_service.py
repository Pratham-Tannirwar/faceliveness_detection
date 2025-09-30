"""
KYC service
"""

from datetime import datetime
from app.models import KYCSubmission, Session
from app.services.face_detection_service import FaceDetectionService
from app import db

class KYCService:
    """Service for handling KYC operations"""
    
    def __init__(self):
        self.face_detection_service = FaceDetectionService()
    
    def submit_kyc(self, user_id, session_id, document_images, selfie_image):
        """Submit KYC documents for verification"""
        try:
            # Verify session exists and belongs to user
            session = Session.query.filter_by(id=session_id, user_id=user_id).first()
            if not session:
                return {'success': False, 'message': 'Session not found or access denied'}
            
            # Check if user already has a pending KYC submission
            existing_submission = KYCSubmission.query.filter_by(
                user_id=user_id,
                status='pending'
            ).first()
            
            if existing_submission:
                return {'success': False, 'message': 'You already have a pending KYC submission'}
            
            # Perform liveness check on selfie
            liveness_result = self.perform_liveness_check(user_id, session_id, selfie_image)
            
            if not liveness_result['success']:
                return liveness_result
            
            # Create KYC submission
            kyc_submission = KYCSubmission(
                user_id=user_id,
                liveness_result=liveness_result['data']['liveness_result']['is_live'],
                status='pending'
            )
            
            db.session.add(kyc_submission)
            db.session.commit()
            
            return {
                'success': True,
                'data': kyc_submission.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'KYC submission failed: {str(e)}'}
    
    def perform_liveness_check(self, user_id, session_id, image_data):
        """Perform liveness check for KYC"""
        try:
            # Use face detection service for liveness check
            result = self.face_detection_service.liveness_check(session_id, user_id, image_data)
            
            if not result['success']:
                return result
            
            liveness_data = result['data']['liveness_result']
            
            # Determine liveness result
            is_live = liveness_data.get('is_live', False)
            confidence = liveness_data.get('confidence', 0.0)
            
            liveness_status = 'passed' if is_live and confidence > 0.7 else 'failed'
            
            return {
                'success': True,
                'data': {
                    'liveness_result': {
                        'is_live': is_live,
                        'confidence': confidence,
                        'status': liveness_status
                    },
                    'detection': result['data']['detection']
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Liveness check failed: {str(e)}'}
    
    def create_kyc_session(self, user_id):
        """Create a new KYC session for the user"""
        try:
            # Create a new session for KYC verification
            session = Session(
                user_id=user_id,
                session_type='kyc',
                status='active'
            )
            
            db.session.add(session)
            db.session.commit()
            
            return session
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Failed to create KYC session: {str(e)}')
    
    def get_kyc_status(self, user_id):
        """Get user's KYC status"""
        try:
            kyc_submission = KYCSubmission.query.filter_by(user_id=user_id).order_by(
                KYCSubmission.submitted_at.desc()
            ).first()
            
            if not kyc_submission:
                return {
                    'success': True,
                    'data': {
                        'status': 'not_submitted',
                        'message': 'No KYC submission found'
                    }
                }
            
            return {
                'success': True,
                'data': kyc_submission.to_dict()
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to get KYC status: {str(e)}'}
    
    def update_kyc_status(self, submission_id, status, notes=None):
        """Update KYC submission status (admin function)"""
        try:
            kyc_submission = KYCSubmission.query.get(submission_id)
            
            if not kyc_submission:
                return {'success': False, 'message': 'KYC submission not found'}
            
            kyc_submission.status = status
            kyc_submission.reviewed_at = datetime.utcnow()
            
            if notes:
                kyc_submission.notes = notes
            
            db.session.commit()
            
            return {
                'success': True,
                'data': kyc_submission.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Failed to update KYC status: {str(e)}'}
