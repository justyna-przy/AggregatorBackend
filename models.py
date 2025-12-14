from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class EventType(db.Model):
    """Lookup table for all possible event types"""
    __tablename__ = 'event_types'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relationship to events
    events = db.relationship('Event', backref='event_type_ref', lazy=True)
    
    def __repr__(self):
        return f'<EventType {self.event_type}>'


class Event(db.Model):
    """Records each event occurrence with timestamp"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type_id = db.Column(db.Integer, db.ForeignKey('event_types.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    floor = db.Column(db.Integer, nullable=True)  # Optional: for events related to specific floors
    
    def __repr__(self):
        return f'<Event {self.id}: {self.event_type_ref.event_type} at {self.timestamp}>'


# Event type constants matching your embedded system
EVENT_TYPES = [
    'floor_reached_0',
    'floor_reached_1', 
    'floor_reached_2',
    'button_inside_0',
    'button_inside_1',
    'button_inside_2',
    'call_button_0_up',
    'call_button_1_up',
    'call_button_1_down',
    'call_button_2_down',
    'emergency_stop',
    'emergency_released',
    'maxim_connected',         # MAX32655 connected to ESP32
    'maxim_connection_lost'    # Heartbeat timeout
]
