"""
Users API endpoints
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User
from app.services.user_service import UserService

users_ns = Namespace('users', description='User operations')

# Response models
user_model = users_ns.model('User', {
    'id': fields.Integer(description='User ID'),
    'fullname': fields.String(description='Full name'),
    'email': fields.String(description='Email address'),
    'mobile_number': fields.String(description='Mobile number'),
    'account_number': fields.String(description='Account number'),
    'account_type': fields.String(description='Account type'),
    'balance': fields.Float(description='Account balance'),
    'is_active': fields.Boolean(description='Account status'),
    'created_at': fields.String(description='Creation date'),
    'updated_at': fields.String(description='Last update date')
})

update_profile_model = users_ns.model('UpdateProfile', {
    'fullname': fields.String(description='Full name'),
    'email': fields.String(description='Email address'),
    'mobile_number': fields.String(description='Mobile number')
})

@users_ns.route('/profile')
class UserProfile(Resource):
    @jwt_required()
    @users_ns.marshal_with(user_model)
    def get(self):
        """Get current user profile"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'message': 'User not found'}, 404
            
            return user.to_dict(), 200
            
        except Exception as e:
            return {'message': f'Failed to get profile: {str(e)}'}, 500
    
    @jwt_required()
    @users_ns.expect(update_profile_model)
    @users_ns.marshal_with(user_model)
    def put(self):
        """Update user profile"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            user_service = UserService()
            result = user_service.update_profile(current_user_id, data)
            
            if result['success']:
                return result['data'], 200
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Failed to update profile: {str(e)}'}, 500

@users_ns.route('/<int:user_id>')
class UserById(Resource):
    @jwt_required()
    @users_ns.marshal_with(user_model)
    def get(self, user_id):
        """Get user by ID"""
        try:
            current_user_id = get_jwt_identity()
            
            # Users can only view their own profile or admin can view any
            if current_user_id != user_id:
                # Add admin check here if needed
                return {'message': 'Access denied'}, 403
            
            user = User.query.get(user_id)
            
            if not user:
                return {'message': 'User not found'}, 404
            
            return user.to_dict(), 200
            
        except Exception as e:
            return {'message': f'Failed to get user: {str(e)}'}, 500

@users_ns.route('/change-password')
class ChangePassword(Resource):
    @jwt_required()
    def post(self):
        """Change user password"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            
            if not current_password or not new_password:
                return {'message': 'Current password and new password are required'}, 400
            
            user_service = UserService()
            result = user_service.change_password(current_user_id, current_password, new_password)
            
            if result['success']:
                return result['data'], 200
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Failed to change password: {str(e)}'}, 500
