"""
Flask API application package
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=None):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        from app.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Register blueprints
    from app.api.v1 import api_v1_bp
    app.register_blueprint(api_v1_bp)
    
    # Add basic routes
    @app.route('/')
    def root():
        return {'message': 'FaceLive Flask API', 'version': '1.0.0'}
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'FaceLive Flask API'}
    
    return app
