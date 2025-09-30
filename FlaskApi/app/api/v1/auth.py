"""
Authentication API endpoints
"""

from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models import User, OTPVerification
from app.services.auth_service import AuthService
from app.utils.validators import validate_email, validate_mobile_number

auth_ns = Namespace('auth', description='Authentication operations')

# Request/Response models
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

signup_model = auth_ns.model('Signup', {
    'fullname': fields.String(required=True, description='Full name'),
    'email': fields.String(required=True, description='Email address'),
    'mobile_number': fields.String(required=True, description='Mobile number'),
    'password': fields.String(required=True, description='Password')
})

otp_request_model = auth_ns.model('OTPRequest', {
    'mobile_number': fields.String(required=True, description='Mobile number'),
    'purpose': fields.String(required=True, description='OTP purpose (signup/login)')
})

otp_verify_model = auth_ns.model('OTPVerify', {
    'mobile_number': fields.String(required=True, description='Mobile number'),
    'otp_code': fields.String(required=True, description='OTP code'),
    'purpose': fields.String(required=True, description='OTP purpose')
})

token_response_model = auth_ns.model('TokenResponse', {
    'access_token': fields.String(description='Access token'),
    'refresh_token': fields.String(description='Refresh token'),
    'user': fields.Raw(description='User information')
})

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        """User login"""
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return {'success': False, 'message': 'Email and password are required'}, 400
            
            if not validate_email(email):
                return {'success': False, 'message': 'Invalid email format'}, 400
            
            auth_service = AuthService()
            result = auth_service.login(email, password)
            
            if result['success']:
                return {
                    'success': True,
                    'access_token': result['data']['access_token'],
                    'refresh_token': result['data']['refresh_token'],
                    'user': result['data']['user']
                }, 200
            else:
                return {
                    'success': False,
                    'access_token': None,
                    'refresh_token': None,
                    'user': None,
                    'message': result['message']
                }, 401
                
        except Exception as e:
            return {
                'success': False,
                'access_token': None,
                'refresh_token': None,
                'user': None,
                'message': f'Login failed: {str(e)}'
            }, 500

@auth_ns.route('/signup')
class Signup(Resource):
    @auth_ns.expect(signup_model)
    def post(self):
        """User registration"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['fullname', 'email', 'mobile_number', 'password']
            for field in required_fields:
                if not data.get(field):
                    return {'message': f'{field} is required'}, 400
            
            # Validate email and mobile number
            if not validate_email(data['email']):
                return {'message': 'Invalid email format'}, 400
            
            if not validate_mobile_number(data['mobile_number']):
                return {'message': 'Invalid mobile number format'}, 400
            
            auth_service = AuthService()
            result = auth_service.signup(
                data['fullname'],
                data['email'],
                data['mobile_number'],
                data['password']
            )
            
            if result['success']:
                return result['data'], 201
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Signup failed: {str(e)}'}, 500

@auth_ns.route('/send-otp')
class SendOTP(Resource):
    @auth_ns.expect(otp_request_model)
    def post(self):
        """Send OTP to mobile number"""
        try:
            data = request.get_json()
            mobile_number = data.get('mobile_number')
            purpose = data.get('purpose')
            
            if not mobile_number or not purpose:
                return {'message': 'Mobile number and purpose are required'}, 400
            
            if not validate_mobile_number(mobile_number):
                return {'message': 'Invalid mobile number format'}, 400
            
            if purpose not in ['signup', 'login', 'reset_password']:
                return {'message': 'Invalid purpose. Must be signup, login, or reset_password'}, 400
            
            auth_service = AuthService()
            result = auth_service.send_otp(mobile_number, purpose)
            
            if result['success']:
                return result['data'], 200
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Failed to send OTP: {str(e)}'}, 500

@auth_ns.route('/send-otp-test')
class SendOTPTest(Resource):
    @auth_ns.expect(otp_request_model)
    def post(self):
        """Test endpoint to send OTP to mobile number (for testing only)"""
        try:
            data = request.get_json()
            mobile_number = data.get('mobile_number')
            purpose = data.get('purpose')
            
            if not mobile_number or not purpose:
                return {'message': 'Mobile number and purpose are required'}, 400
            
            # Generate a fixed OTP for testing
            test_otp = '123456'
            
            # Return success with the test OTP
            return {
                'message': 'OTP sent successfully',
                'otp_code': test_otp,
                'expires_in_minutes': 10
            }, 200
                
        except Exception as e:
            return {'message': f'Failed to send OTP: {str(e)}'}, 500

@auth_ns.route('/verify-otp')
class VerifyOTP(Resource):
    @auth_ns.expect(otp_verify_model)
    def post(self):
        """Verify OTP code"""
        try:
            data = request.get_json()
            mobile_number = data.get('mobile_number')
            otp_code = data.get('otp_code')
            purpose = data.get('purpose')
            
            if not all([mobile_number, otp_code, purpose]):
                return {'message': 'Mobile number, OTP code, and purpose are required'}, 400
            
            auth_service = AuthService()
            result = auth_service.verify_otp(mobile_number, otp_code, purpose)
            
            if result['success']:
                return result['data'], 200
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'OTP verification failed: {str(e)}'}, 500

@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """Refresh access token"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'message': 'User not found'}, 404
            
            new_access_token = create_access_token(identity=str(current_user_id))
            
            return {
                'access_token': new_access_token,
                'user': user.to_dict()
            }, 200
            
        except Exception as e:
            return {'message': f'Token refresh failed: {str(e)}'}, 500

@auth_ns.route('/verify-otp-test')
class VerifyOTPTest(Resource):
    @auth_ns.expect(otp_verify_model)
    def post(self):
        """Test endpoint to verify OTP code without actual validation (for testing only)"""
        try:
            data = request.get_json()
            mobile_number = data.get('mobile_number')
            otp_code = data.get('otp_code')
            purpose = data.get('purpose')
            
            if not all([mobile_number, otp_code, purpose]):
                return {'message': 'Mobile number, OTP code, and purpose are required'}, 400
            
            # Always return success for testing
            return {
                'message': 'OTP verified successfully',
                'verified': True
            }, 200
                
        except Exception as e:
            return {'message': f'OTP verification failed: {str(e)}'}, 500

@auth_ns.route('/logout')
class Logout(Resource):
    @jwt_required()
    def post(self):
        """User logout"""
        try:
            # In a real application, you would add the token to a blacklist
            return {'message': 'Successfully logged out'}, 200
        except Exception as e:
            return {'message': f'Logout failed: {str(e)}'}, 500
