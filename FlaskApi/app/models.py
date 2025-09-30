"""
Database models for Flask API
"""

from datetime import datetime
from app import db
# from sqlalchemy.dialects.postgresql import JSONB  # PostgreSQL specific

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(20), unique=True)
    account_type = db.Column(db.String(20), default='standard')
    balance = db.Column(db.Numeric(15, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='user', lazy=True, cascade='all, delete-orphan')
    face_detections = db.relationship('FaceDetection', backref='user', lazy=True, cascade='all, delete-orphan')
    kyc_submissions = db.relationship('KYCSubmission', backref='user', lazy=True, cascade='all, delete-orphan')
    # otp_verifications = db.relationship('OTPVerification', backref='user', lazy=True, cascade='all, delete-orphan')  # No foreign key relationship
    
    def to_dict(self):
        return {
            'id': self.id,
            'fullname': self.fullname,
            'email': self.email,
            'mobile_number': self.mobile_number,
            'account_number': self.account_number,
            'account_type': self.account_type,
            'balance': float(self.balance) if self.balance else 0.0,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Session(db.Model):
    """Session model for live streaming and KYC"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_name = db.Column(db.String(100), nullable=True)
    room_id = db.Column(db.String(50), unique=True, nullable=True)
    session_type = db.Column(db.String(20), default='streaming')
    status = db.Column(db.String(20), default='active')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    # Relationships
    face_detections = db.relationship('FaceDetection', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_name': self.session_name,
            'room_id': self.room_id,
            'session_type': self.session_type,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }

class FaceDetection(db.Model):
    """Face detection results model"""
    __tablename__ = 'face_detections'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    face_data = db.Column(db.Text)  # JSON as text for SQLite compatibility
    confidence_score = db.Column(db.Numeric(5, 4))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'face_data': self.face_data,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class KYCSubmission(db.Model):
    """KYC submission model"""
    __tablename__ = 'kyc_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    liveness_result = db.Column(db.String(20), default='pending')
    status = db.Column(db.String(20), default='pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'liveness_result': self.liveness_result,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'notes': self.notes
        }

class OTPVerification(db.Model):
    """OTP verification model"""
    __tablename__ = 'otp_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100))
    otp_code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'mobile_number': self.mobile_number,
            'email': self.email,
            'otp_code': self.otp_code,
            'purpose': self.purpose,
            'is_verified': self.is_verified,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
