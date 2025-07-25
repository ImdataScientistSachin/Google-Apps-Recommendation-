from flask import Flask
from flask_cors import CORS
import os
import logging
import traceback
from flask_sqlalchemy import SQLAlchemy
from app.models import db

def create_app(test_config=None):
    """Create and configure Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    if test_config is None:
        app.config.from_object('app.config.Config')
    else:
        app.config.from_mapping(test_config)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register routes
    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    # Verify paths before initializing recommender
    from app.config import Config
    missing_files = Config.verify_paths()
    if missing_files:
        app.logger.critical(f"Missing required files: {missing_files}")
        app.recommender = None
        return app
    
    # Initialize recommender
    try:
        from .recommender import AppRecommender
        app.recommender = AppRecommender()
        app.logger.info("Successfully initialized recommender")
        # IMPORTANT: Removed the line that was setting recommender to None
    except Exception as e:
        app.recommender = None  # Explicitly set to None only on error
        app.logger.critical(f"Fatal initialization error: {str(e)}")
        app.logger.critical(f"Stack trace: {traceback.format_exc()}")
        # Don't re-raise the exception - allow the app to start

    return app