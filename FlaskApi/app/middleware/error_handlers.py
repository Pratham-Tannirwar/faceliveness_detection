"""
Error handlers for Flask API
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    """Register error handlers with Flask app"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': 'The request was invalid or cannot be served',
            'code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authentication is required',
            'code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'Access to this resource is forbidden',
            'code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'code': 404
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for this resource',
            'code': 405
        }), 405
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'success': False,
            'error': 'Unprocessable Entity',
            'message': 'The request was well-formed but contains semantic errors',
            'code': 422
        }), 422
    
    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({
            'success': False,
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded',
            'code': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred',
            'code': 500
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            'success': False,
            'error': error.name,
            'message': error.description,
            'code': error.code
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        app.logger.error(f'Unhandled exception: {str(error)}')
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'code': 500
        }), 500
