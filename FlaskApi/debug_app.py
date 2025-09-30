#!/usr/bin/env python3
"""
Debug app creation step by step
"""

import os
import sys
from flask import Flask

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for SQLite
os.environ['DATABASE_URL'] = 'sqlite:///test.db'
os.environ['FLASK_DEBUG'] = 'True'

try:
    print("Step 1: Importing Flask...")
    from flask import Flask, jsonify
    print("[OK] Flask imported")
    
    print("Step 2: Importing extensions...")
    from flask_cors import CORS
    from flask_migrate import Migrate
    print("[OK] Extensions imported")
    
    print("Step 3: Importing config...")
    from app.config import Config
    print("[OK] Config imported")
    
    print("Step 4: Importing models...")
    from app.models import db
    print("[OK] Models imported")
    
    print("Step 5: Importing API blueprint...")
    from app.api.v1 import api_v1_bp
    print("[OK] API blueprint imported")
    
    print("Step 6: Importing error handlers...")
    from app.middleware.error_handlers import register_error_handlers
    print("[OK] Error handlers imported")
    
    print("Step 7: Creating Flask app...")
    app = Flask(__name__)
    print("[OK] Flask app created")
    
    print("Step 8: Loading config...")
    app.config.from_object(Config)
    print("[OK] Config loaded")
    
    print("Step 9: Initializing database...")
    db.init_app(app)
    print("[OK] Database initialized")
    
    print("Step 10: Initializing migrate...")
    migrate = Migrate(app, db)
    print("[OK] Migrate initialized")
    
    print("Step 11: Initializing CORS...")
    CORS(app, origins=["http://localhost:3001", "http://localhost:8000"])
    print("[OK] CORS initialized")
    
    print("Step 12: Registering API blueprint...")
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    print("[OK] API blueprint registered")
    
    print("Step 13: Registering error handlers...")
    register_error_handlers(app)
    print("[OK] Error handlers registered")
    
    print("Step 14: Adding routes...")
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'FaceLive Flask API',
            'version': '1.0.0'
        })
    
    @app.route('/')
    def root():
        return jsonify({
            'message': 'FaceLive Flask API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'api_v1': '/api/v1',
                'docs': '/api/v1/docs'
            }
        })
    print("[OK] Routes added")
    
    print("\nFinal routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    
    print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")
    
except Exception as e:
    print(f"[ERROR] Error at step: {e}")
    import traceback
    traceback.print_exc()
