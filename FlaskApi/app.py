#!/usr/bin/env python3
"""
FaceLive Flask API
Main application entry point
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from app import create_app as app_create_app

def create_app(config_class=None):
    """Application factory pattern"""
    print("Creating Flask app...")
    app = app_create_app(config_class)
    print("Initializing CORS...")
    CORS(app, origins=["http://localhost:3001", "http://localhost:8000"])
    
    # Register error handlers
    print("Registering error handlers...")
    from app.middleware.error_handlers import register_error_handlers
    register_error_handlers(app)
    print("Error handlers registered")
    
    print("App creation completed")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
