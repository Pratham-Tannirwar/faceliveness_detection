"""
Authentication service
"""

import bcrypt
import secrets
import string
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models import User, OTPVerification
from app import db

class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self):
        self.otp_expiry_minutes = 10
    
    def hash_password(self, password):
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password, hashed_password):
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def generate_otp(self, length=6):
        """Generate a random OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    def login(self, email, password):
        """Authenticate user login"""
        try:
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return {'success': False, 'message': 'Invalid email or password'}
            
            if not self.verify_password(password, user.password_hash):
                return {'success': False, 'message': 'Invalid email or password'}
            
            if not user.is_active:
                return {'success': False, 'message': 'Account is deactivated'}
            
            # Generate tokens (JWT subject must be a string)
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'success': True,
                'data': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': user.to_dict()
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Login failed: {str(e)}'}
    
    def signup(self, fullname, email, mobile_number, password):
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = User.query.filter(
                (User.email == email) | (User.mobile_number == mobile_number)
            ).first()
            
            if existing_user:
                if existing_user.email == email:
                    return {'success': False, 'message': 'Email already registered'}
                else:
                    return {'success': False, 'message': 'Mobile number already registered'}
            
            # Create new user
            hashed_password = self.hash_password(password)
            user = User(
                fullname=fullname,
                email=email,
                mobile_number=mobile_number,
                password_hash=hashed_password
            )
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True,
                'data': {
                    'message': 'User registered successfully',
                    'user': user.to_dict()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Registration failed: {str(e)}'}
    
    def send_otp(self, mobile_number, purpose):
        """Send OTP to mobile number"""
        try:
            # Generate OTP
            otp_code = self.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
            
            # Create OTP record
            otp_verification = OTPVerification(
                mobile_number=mobile_number,
                otp_code=otp_code,
                purpose=purpose,
                expires_at=expires_at
            )
            
            db.session.add(otp_verification)
            db.session.commit()
            
            # In a real application, you would send SMS here
            # For now, we'll just return the OTP for testing
            return {
                'success': True,
                'data': {
                    'message': 'OTP sent successfully',
                    'otp_code': otp_code,  # Remove this in production
                    'expires_in_minutes': self.otp_expiry_minutes
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Failed to send OTP: {str(e)}'}
    
    def verify_otp(self, mobile_number, otp_code, purpose):
        """Verify OTP code"""
        try:
            # Find valid OTP
            otp_verification = OTPVerification.query.filter_by(
                mobile_number=mobile_number,
                otp_code=otp_code,
                purpose=purpose,
                is_verified=False
            ).filter(OTPVerification.expires_at > datetime.utcnow()).first()
            
            if not otp_verification:
                return {'success': False, 'message': 'Invalid or expired OTP'}
            
            # Mark OTP as verified
            otp_verification.is_verified = True
            db.session.commit()
            
            return {
                'success': True,
                'data': {
                    'message': 'OTP verified successfully',
                    'verified': True
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'OTP verification failed: {str(e)}'}
