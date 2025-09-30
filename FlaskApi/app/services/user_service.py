"""
User service
"""

from app.models import User
from app.services.auth_service import AuthService
from app import db

class UserService:
    """Service for handling user operations"""
    
    def __init__(self):
        self.auth_service = AuthService()
    
    def update_profile(self, user_id, data):
        """Update user profile"""
        try:
            user = User.query.get(user_id)
            
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Update allowed fields
            if 'fullname' in data:
                user.fullname = data['fullname']
            
            if 'email' in data:
                # Check if email is already taken
                existing_user = User.query.filter(
                    User.email == data['email'],
                    User.id != user_id
                ).first()
                
                if existing_user:
                    return {'success': False, 'message': 'Email already in use'}
                
                user.email = data['email']
            
            if 'mobile_number' in data:
                # Check if mobile number is already taken
                existing_user = User.query.filter(
                    User.mobile_number == data['mobile_number'],
                    User.id != user_id
                ).first()
                
                if existing_user:
                    return {'success': False, 'message': 'Mobile number already in use'}
                
                user.mobile_number = data['mobile_number']
            
            db.session.commit()
            
            return {
                'success': True,
                'data': user.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Failed to update profile: {str(e)}'}
    
    def change_password(self, user_id, current_password, new_password):
        """Change user password"""
        try:
            user = User.query.get(user_id)
            
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Verify current password
            if not self.auth_service.verify_password(current_password, user.password_hash):
                return {'success': False, 'message': 'Current password is incorrect'}
            
            # Hash new password
            new_password_hash = self.auth_service.hash_password(new_password)
            user.password_hash = new_password_hash
            
            db.session.commit()
            
            return {
                'success': True,
                'data': {'message': 'Password changed successfully'}
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Failed to change password: {str(e)}'}
