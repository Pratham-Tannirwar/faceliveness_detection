"""
Session service
"""

import secrets
import string
from app.models import Session, User
from app import db

class SessionService:
    """Service for handling session operations"""
    
    def generate_room_id(self, length=8):
        """Generate a random room ID"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def create_session(self, user_id, session_name, custom_room_id=None):
        """Create a new session"""
        try:
            user = User.query.get(user_id)
            
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Generate room ID if not provided
            room_id = custom_room_id or self.generate_room_id()
            
            # Check if room ID already exists
            existing_session = Session.query.filter_by(room_id=room_id, is_active=True).first()
            if existing_session:
                if custom_room_id:
                    return {'success': False, 'message': 'Room ID already in use'}
                else:
                    # Generate a new room ID
                    room_id = self.generate_room_id()
            
            # Create session
            session = Session(
                user_id=user_id,
                session_name=session_name,
                room_id=room_id,
                is_active=True
            )
            
            db.session.add(session)
            db.session.commit()
            
            return {
                'success': True,
                'data': session.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Failed to create session: {str(e)}'}
    
    def end_session(self, session_id, user_id):
        """End a session"""
        try:
            session = Session.query.filter_by(id=session_id, user_id=user_id).first()
            
            if not session:
                return {'success': False, 'message': 'Session not found'}
            
            if not session.is_active:
                return {'success': False, 'message': 'Session is already ended'}
            
            session.is_active = False
            db.session.commit()
            
            return {
                'success': True,
                'data': {'message': 'Session ended successfully'}
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Failed to end session: {str(e)}'}
    
    def join_session(self, room_id, user_id):
        """Join an existing session by room ID"""
        try:
            session = Session.query.filter_by(room_id=room_id, is_active=True).first()
            
            if not session:
                return {'success': False, 'message': 'Session not found or inactive'}
            
            # Check if user is already the owner
            if session.user_id == user_id:
                return {
                    'success': True,
                    'data': session.to_dict()
                }
            
            # In a real application, you might want to add participants table
            # For now, we'll just return the session info
            return {
                'success': True,
                'data': session.to_dict()
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to join session: {str(e)}'}
