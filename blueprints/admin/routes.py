from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from ..models import Guest
from .. import db
import os

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if (username == os.environ.get('ADMIN_USERNAME', 'admin') and 
            password == os.environ.get('ADMIN_PASSWORD', 'password')):
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('public.index'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    guests = Guest.query.all()
    total_guests = len(guests)
    attending = len([g for g in guests if g.rsvp_status == 1])
    not_attending = len([g for g in guests if g.rsvp_status == 2])
    pending = len([g for g in guests if g.rsvp_status == 0])
    
    return render_template('admin/dashboard.html', 
                         guests=guests,
                         total_guests=total_guests,
                         attending=attending,
                         not_attending=not_attending,
                         pending=pending)

@admin_bp.route('/guests')
@admin_required
def guests():
    """Guest management page"""
    guests = Guest.query.all()
    return render_template('admin/guests.html', guests=guests)

@admin_bp.route('/export')
@admin_required
def export():
    """Export guest data to CSV"""
    import csv
    from io import StringIO
    from flask import Response
    
    guests = Guest.query.all()
    
    def generate():
        data = StringIO()
        writer = csv.writer(data)
        
        # Write header
        writer.writerow(['Family Code', 'Name', 'Email', 'RSVP Status', 'Created'])
        
        # Write data
        for guest in guests:
            status = 'Pending'
            if guest.rsvp_status == 1:
                status = 'Attending'
            elif guest.rsvp_status == 2:
                status = 'Not Attending'
            
            writer.writerow([
                guest.family_code,
                guest.name,
                guest.email or '',
                status,
                guest.created_at.strftime('%Y-%m-%d %H:%M:%S') if guest.created_at else ''
            ])
        
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
    
    return Response(generate(), 
                   mimetype='text/csv',
                   headers={'Content-Disposition': 'attachment; filename=guests.csv'})
