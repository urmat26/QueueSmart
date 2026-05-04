from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """User accounts for both Admins and Clients"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='client')  # 'admin' or 'client'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship with tickets (for client history)
    tickets = db.relationship('Ticket', backref='client_user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role
        }


class Service(db.Model):
    """Types of services offered (e.g., General, VIP, Consultation)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), default='')
    estimated_time = db.Column(db.Integer, default=10)  # minutes
    is_active = db.Column(db.Boolean, default=True)
    icon = db.Column(db.String(50), default='📋')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tickets = db.relationship('Ticket', backref='service', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'estimated_time': self.estimated_time,
            'is_active': self.is_active,
            'icon': self.icon
        }


class ServiceWindow(db.Model):
    """Service counters/windows where clients are served"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    current_ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    operator_name = db.Column(db.String(100), default='Оператор')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        ticket = None
        if self.current_ticket_id:
            t = Ticket.query.get(self.current_ticket_id)
            if t:
                ticket = t.to_dict()
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active,
            'current_ticket': ticket,
            'operator_name': self.operator_name
        }


class Ticket(db.Model):
    """Queue ticket for each client"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    client_phone = db.Column(db.String(20), default='')
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    telegram_chat_id = db.Column(db.String(50), nullable=True)
    
    # Status: waiting, called, serving, completed, cancelled, skipped
    status = db.Column(db.String(20), default='waiting')
    position = db.Column(db.Integer, default=0)
    
    window_id = db.Column(db.Integer, db.ForeignKey('service_window.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    called_at = db.Column(db.DateTime, nullable=True)
    served_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Tracking token for client to check status
    token = db.Column(db.String(64), unique=True, nullable=False)

    def to_dict(self):
        wait_time = None
        service_time = None
        if self.called_at and self.created_at:
            wait_time = (self.called_at - self.created_at).total_seconds() / 60
        if self.completed_at and self.served_at:
            service_time = (self.completed_at - self.served_at).total_seconds() / 60
            
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'client_name': self.client_name,
            'client_phone': self.client_phone,
            'service_id': self.service_id,
            'service_name': self.service.name if self.service else '',
            'service_icon': self.service.icon if self.service else '📋',
            'status': self.status,
            'position': self.position,
            'window_id': self.window_id,
            'token': self.token,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'called_at': self.called_at.isoformat() if self.called_at else None,
            'served_at': self.served_at.isoformat() if self.served_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'wait_time_minutes': round(wait_time, 1) if wait_time else None,
            'service_time_minutes': round(service_time, 1) if service_time else None,
        }


class DailyStats(db.Model):
    """Daily aggregated statistics"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_served = db.Column(db.Integer, default=0)
    total_cancelled = db.Column(db.Integer, default=0)
    avg_wait_time = db.Column(db.Float, default=0.0)
    avg_service_time = db.Column(db.Float, default=0.0)
    peak_hour = db.Column(db.Integer, default=0)
    max_queue_length = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_served': self.total_served,
            'total_cancelled': self.total_cancelled,
            'avg_wait_time': round(self.avg_wait_time, 1),
            'avg_service_time': round(self.avg_service_time, 1),
            'peak_hour': self.peak_hour,
            'max_queue_length': self.max_queue_length
        }
