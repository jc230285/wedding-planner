from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import Guest
from .. import db

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    """Main wedding website"""
    return render_template('index.html')

@public_bp.route('/rsvp/<code>', methods=['GET', 'POST'])
def rsvp(code):
    """RSVP page for a specific family code"""
    code = code.upper()
    
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
