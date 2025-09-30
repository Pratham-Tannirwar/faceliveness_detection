#!/usr/bin/env python3
"""
Flask API startup script
"""

import os
from app import create_app

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting FaceLive Flask API on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    
    app.run(host=host, port=port, debug=debug)
