"""
Sessions API endpoints for live streaming
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Session, User
from app.services.session_service import SessionService

sessions_ns = Namespace('sessions', description='Session operations')

# Request/Response models
session_model = sessions_ns.model('Session', {
    'id': fields.Integer(description='Session ID'),
    'user_id': fields.Integer(description='User ID'),
    'session_name': fields.String(description='Session name'),
    'room_id': fields.String(description='Room ID'),
    'is_active': fields.Boolean(description='Session status'),
    'created_at': fields.String(description='Creation date'),
    'ended_at': fields.String(description='End date')
})

create_session_model = sessions_ns.model('CreateSession', {
    'session_name': fields.String(required=True, description='Session name'),
    'room_id': fields.String(description='Custom room ID (optional)')
})

@sessions_ns.route('/')
class Sessions(Resource):
    @jwt_required()
    @sessions_ns.marshal_list_with(session_model)
    def get(self):
        """Get user's sessions"""
        try:
            current_user_id = get_jwt_identity()
            
            sessions = Session.query.filter_by(user_id=current_user_id).order_by(Session.created_at.desc()).all()
            
            return [session.to_dict() for session in sessions], 200
            
        except Exception as e:
            return {'message': f'Failed to get sessions: {str(e)}'}, 500
    
    @jwt_required()
    @sessions_ns.expect(create_session_model)
    @sessions_ns.marshal_with(session_model)
    def post(self):
        """Create a new session"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            session_name = data.get('session_name')
            room_id = data.get('room_id')
            
            if not session_name:
                return {'message': 'Session name is required'}, 400
            
            session_service = SessionService()
            result = session_service.create_session(current_user_id, session_name, room_id)
            
            if result['success']:
                return result['data'], 201
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Failed to create session: {str(e)}'}, 500

@sessions_ns.route('/<int:session_id>')
class SessionById(Resource):
    @jwt_required()
    @sessions_ns.marshal_with(session_model)
    def get(self, session_id):
        """Get session by ID"""
        try:
            current_user_id = get_jwt_identity()
            
            session = Session.query.filter_by(id=session_id, user_id=current_user_id).first()
            
            if not session:
                return {'message': 'Session not found'}, 404
            
            return session.to_dict(), 200
            
        except Exception as e:
            return {'message': f'Failed to get session: {str(e)}'}, 500
    
    @jwt_required()
    def delete(self, session_id):
        """End a session"""
        try:
            current_user_id = get_jwt_identity()
            
            session_service = SessionService()
            result = session_service.end_session(session_id, current_user_id)
            
            if result['success']:
                return result['data'], 200
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Failed to end session: {str(e)}'}, 500

@sessions_ns.route('/join/<string:room_id>')
class JoinSession(Resource):
    @jwt_required()
    @sessions_ns.marshal_with(session_model)
    def post(self, room_id):
        """Join an existing session by room ID"""
        try:
            current_user_id = get_jwt_identity()
            
            session_service = SessionService()
            result = session_service.join_session(room_id, current_user_id)
            
            if result['success']:
                return result['data'], 200
            else:
                return {'message': result['message']}, 400
                
        except Exception as e:
            return {'message': f'Failed to join session: {str(e)}'}, 500

@sessions_ns.route('/active')
class ActiveSessions(Resource):
    @jwt_required()
    @sessions_ns.marshal_list_with(session_model)
    def get(self):
        """Get user's active sessions"""
        try:
            current_user_id = get_jwt_identity()
            
            sessions = Session.query.filter_by(user_id=current_user_id, is_active=True).all()
            
            return [session.to_dict() for session in sessions], 200
            
        except Exception as e:
            return {'message': f'Failed to get active sessions: {str(e)}'}, 500
