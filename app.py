#!/usr/bin/env python3
"""
Wedding Planner Flask Application
A simple RSVP management system for weddings
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import csv

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Enhanced logging configuration
    import logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    app.logger.info("=== FLASK APPLICATION STARTUP ===")
    app.logger.info(f"Flask environment: {os.environ.get('FLASK_ENV', 'Not set')}")
    app.logger.info(f"Debug mode: {os.environ.get('FLASK_DEBUG', 'Not set')}")
    app.logger.info(f"Domain: {os.environ.get('DOMAIN', 'Not set')}")
    app.logger.info(f"Secret key configured: {'Yes' if os.environ.get('SECRET_KEY') else 'No'}")

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///wedding.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Admin configuration
    app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'admin')
    app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'password')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from blueprints.public import public_bp
    from blueprints.admin import admin_bp
    from blueprints.api import api_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        app.logger.info("Creating database tables if they don't exist...")
        # Create tables if they don't exist
        db.create_all()
        app.logger.info("Database tables created successfully")

    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    app.logger.info(f"Starting Flask development server on port {port}")
    app.logger.info(f"Debug mode: {debug}")
    app.logger.info(f"Health check: http://localhost:{port}/health")
    app.logger.info("=== APPLICATION STARTUP COMPLETE ===")

    app.run(host='0.0.0.0', port=port, debug=debug)