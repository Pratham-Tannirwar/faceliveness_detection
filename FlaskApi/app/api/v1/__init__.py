"""
API v1 Blueprint
"""

from flask import Blueprint
from flask_restx import Api

# Create API v1 blueprint
api_v1_bp = Blueprint('api_v1', __name__)

# Create Flask-RESTx API instance
api = Api(
    api_v1_bp,
    version='1.0',
    title='FaceLive API v1',
    description='FaceLive Flask API for face detection and live streaming',
    doc='/docs/',
    prefix='/api/v1'
)

# Import and register namespaces
from .auth import auth_ns
from .users import users_ns
from .sessions import sessions_ns
from .face_detection import face_detection_ns
from .kyc import kyc_ns
from .liveness import liveness_ns

# Register namespaces
api.add_namespace(auth_ns)
api.add_namespace(users_ns)
api.add_namespace(sessions_ns)
api.add_namespace(face_detection_ns)
api.add_namespace(kyc_ns)
api.add_namespace(liveness_ns)
