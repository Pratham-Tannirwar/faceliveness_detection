"""
Validation utilities
"""

import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_mobile_number(mobile_number: str) -> bool:
    """Validate mobile number format"""
    if not mobile_number:
        return False
    
    # Remove any non-digit characters
    digits_only = re.sub(r'\D', '', mobile_number)
    
    # Check if it's a valid mobile number (10-15 digits)
    return 10 <= len(digits_only) <= 15

def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, None

def validate_name(name: str) -> bool:
    """Validate name format"""
    if not name:
        return False
    
    # Name should contain only letters, spaces, hyphens, and apostrophes
    pattern = r"^[a-zA-Z\s\-']+$"
    return re.match(pattern, name) is not None and len(name.strip()) >= 2

def validate_room_id(room_id: str) -> bool:
    """Validate room ID format"""
    if not room_id:
        return False
    
    # Room ID should be alphanumeric, 4-20 characters
    pattern = r'^[a-zA-Z0-9]{4,20}$'
    return re.match(pattern, room_id) is not None

def validate_otp_code(otp_code: str) -> bool:
    """Validate OTP code format"""
    if not otp_code:
        return False
    
    # OTP should be 4-8 digits
    pattern = r'^[0-9]{4,8}$'
    return re.match(pattern, otp_code) is not None

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', text)
    return sanitized.strip()

def validate_image_data(image_data: str) -> bool:
    """Validate base64 image data"""
    if not image_data:
        return False
    
    try:
        # Check if it's valid base64
        import base64
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Try to decode
        base64.b64decode(image_data)
        return True
    except Exception:
        return False
