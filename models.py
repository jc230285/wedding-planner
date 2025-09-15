from datetime import datetime
from . import db

class Guest(db.Model):
    """Guest model for RSVP management"""
    id = db.Column(db.Integer, primary_key=True)
    family_code = db.Column(db.String(10), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    rsvp_status = db.Column(db.Integer, default=0)  # 0=pending, 1=attending, 2=not_attending
    dietary_restrictions = db.Column(db.Text)
    plus_one = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Guest {self.name} ({self.family_code})>'
    
    @property
    def status_text(self):
        """Get human-readable status"""
        if self.rsvp_status == 1:
            return 'Attending'
        elif self.rsvp_status == 2:
            return 'Not Attending'
        else:
            return 'Pending'
