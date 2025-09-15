from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from ..models import Guest
from .. import db
import os
import sys

public_bp = Blueprint('public', __name__)

@public_bp.route('/health')
def health():
    """Health check endpoint for deployment monitoring"""
    import datetime
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'service': 'wedding-planner',
        'version': '1.0.0',
        'port': 5070
    }
    current_app.logger.info(f"Health check requested from {request.remote_addr}")
    return health_data, 200

@public_bp.route('/')
def index():
    """Main wedding website"""
    return render_template('index.html')

@public_bp.route('/debug')
def debug():
    """Debug endpoint for troubleshooting"""
    import datetime
    import os

    debug_info = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'service': 'wedding-planner',
        'version': '1.0.0',
        'environment': {
            'FLASK_ENV': os.environ.get('FLASK_ENV'),
            'FLASK_DEBUG': os.environ.get('FLASK_DEBUG'),
            'DOMAIN': os.environ.get('DOMAIN'),
            'PORT': os.environ.get('PORT', '5070'),
            'SECRET_KEY': '***configured***' if os.environ.get('SECRET_KEY') else 'NOT SET',
            'DATABASE_URL': '***configured***' if os.environ.get('DATABASE_URL') else 'sqlite:///wedding.db'
        },
        'system': {
            'python_version': sys.version,
            'platform': sys.platform,
            'working_directory': os.getcwd()
        },
        'health_endpoints': {
            'health': '/health',
            'debug': '/debug'
        }
    }

    current_app.logger.info(f"Debug info requested: {debug_info}")
    return debug_info, 200
    
    # Find guests with this family code
    guests = Guest.query.filter_by(family_code=code).all()
    
    if not guests:
        flash('Invalid RSVP code. Please check your invitation.', 'error')
        return redirect(url_for('public.index'))
    
    if request.method == 'POST':
        # Process RSVP form
        for guest in guests:
            attending = request.form.get(f'attending_{guest.id}')
            if attending == 'yes':
                guest.rsvp_status = 1
            elif attending == 'no':
                guest.rsvp_status = 2
            else:
                guest.rsvp_status = 0
        
        db.session.commit()
        flash('Thank you for your RSVP!', 'success')
        return redirect(url_for('public.index'))
    
    return render_template('rsvp.html', guests=guests, code=code)
