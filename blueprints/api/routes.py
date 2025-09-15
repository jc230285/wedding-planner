from flask import Blueprint, jsonify, request
from ..models import Guest
from .. import db

api_bp = Blueprint('api', __name__)

@api_bp.route('/guests', methods=['GET'])
def get_guests():
    """Get all guests"""
    guests = Guest.query.all()
    guest_list = []
    
    for guest in guests:
        status = 'pending'
        if guest.rsvp_status == 1:
            status = 'attending'
        elif guest.rsvp_status == 2:
            status = 'not_attending'
        
        guest_list.append({
            'id': guest.id,
            'family_code': guest.family_code,
            'name': guest.name,
            'email': guest.email,
            'rsvp_status': status,
            'created_at': guest.created_at.isoformat() if guest.created_at else None
        })
    
    return jsonify({'guests': guest_list})

@api_bp.route('/guests/<int:guest_id>', methods=['PUT'])
def update_guest(guest_id):
    """Update a guest's RSVP status"""
    guest = Guest.query.get_or_404(guest_id)
    
    data = request.get_json()
    if 'rsvp_status' in data:
        if data['rsvp_status'] == 'attending':
            guest.rsvp_status = 1
        elif data['rsvp_status'] == 'not_attending':
            guest.rsvp_status = 2
        else:
            guest.rsvp_status = 0
        
        db.session.commit()
        
        return jsonify({'success': True, 'guest': {
            'id': guest.id,
            'name': guest.name,
            'rsvp_status': data['rsvp_status']
        }})
    
    return jsonify({'error': 'Invalid data'}), 400

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get RSVP statistics"""
    guests = Guest.query.all()
    
    total = len(guests)
    attending = len([g for g in guests if g.rsvp_status == 1])
    not_attending = len([g for g in guests if g.rsvp_status == 2])
    pending = len([g for g in guests if g.rsvp_status == 0])
    
    return jsonify({
        'total_guests': total,
        'attending': attending,
        'not_attending': not_attending,
        'pending': pending,
        'response_rate': round(((total - pending) / total * 100), 1) if total > 0 else 0
    })
