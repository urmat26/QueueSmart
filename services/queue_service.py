from models import db, Ticket, Service, ServiceWindow
from datetime import datetime, timezone
from services.telegram_service import TelegramService
import uuid
import secrets


class QueueService:
    """Core business logic for queue management"""

    @staticmethod
    def generate_ticket_number(service_id):
        """Generate ticket number like A-001, B-002, etc."""
        service = Service.query.get(service_id)
        if not service:
            return None
        prefix = service.name[0].upper()
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        count = Ticket.query.filter(
            Ticket.service_id == service_id,
            Ticket.created_at >= today_start
        ).count()
        return f"{prefix}-{count + 1:03d}"

    @staticmethod
    def create_ticket(client_name, client_phone, service_id):
        """Register a new client in the queue"""
        service = Service.query.get(service_id)
        if not service or not service.is_active:
            return None, "Услуга недоступна"

        # Count current waiting tickets
        waiting_count = Ticket.query.filter_by(
            service_id=service_id,
            status='waiting'
        ).count()

        ticket_number = QueueService.generate_ticket_number(service_id)
        token = secrets.token_urlsafe(32)

        ticket = Ticket(
            ticket_number=ticket_number,
            client_name=client_name,
            client_phone=client_phone,
            service_id=service_id,
            status='waiting',
            position=waiting_count + 1,
            token=token
        )
        db.session.add(ticket)
        db.session.commit()

        return ticket, None

    @staticmethod
    def get_queue_status(service_id=None):
        """Get current queue status"""
        query = Ticket.query.filter(Ticket.status.in_(['waiting', 'called', 'serving']))
        if service_id:
            query = query.filter_by(service_id=service_id)
        
        tickets = query.order_by(Ticket.created_at.asc()).all()
        
        waiting = [t for t in tickets if t.status == 'waiting']
        serving = [t for t in tickets if t.status in ('called', 'serving')]

        return {
            'waiting': [t.to_dict() for t in waiting],
            'serving': [t.to_dict() for t in serving],
            'total_waiting': len(waiting),
            'total_serving': len(serving)
        }

    @staticmethod
    def call_next(window_id, service_id=None):
        """Call the next client in queue to a specific window"""
        window = ServiceWindow.query.get(window_id)
        if not window or not window.is_active:
            return None, "Окно обслуживания недоступно"

        # Find next waiting ticket
        query = Ticket.query.filter_by(status='waiting')
        if service_id:
            query = query.filter_by(service_id=service_id)
        
        next_ticket = query.order_by(Ticket.created_at.asc()).first()
        
        if not next_ticket:
            return None, "Очередь пуста"

        now = datetime.now(timezone.utc)
        next_ticket.status = 'called'
        next_ticket.called_at = now
        next_ticket.window_id = window_id
        window.current_ticket_id = next_ticket.id
        
        # Recalculate positions for waiting tickets
        QueueService._recalculate_positions(next_ticket.service_id)
        
        db.session.commit()
        
        # Send Telegram Notification
        # TelegramService.notify_ticket_called(next_ticket)
        
        return next_ticket, None

    @staticmethod
    def link_telegram(ticket_id, chat_id):
        """Link a telegram chat ID to a ticket"""
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return False, "Талон не найден"
        
        ticket.telegram_chat_id = str(chat_id)
        db.session.commit()
        return True, None

    @staticmethod
    def start_serving(ticket_id):
        """Mark ticket as being served"""
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return None, "Талон не найден"
        
        ticket.status = 'serving'
        ticket.served_at = datetime.now(timezone.utc)
        db.session.commit()
        return ticket, None

    @staticmethod
    def complete_ticket(ticket_id):
        """Mark ticket as completed"""
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return None, "Талон не найден"

        ticket.status = 'completed'
        ticket.completed_at = datetime.now(timezone.utc)

        # Clear window
        if ticket.window_id:
            window = ServiceWindow.query.get(ticket.window_id)
            if window:
                window.current_ticket_id = None

        QueueService._recalculate_positions(ticket.service_id)
        db.session.commit()
        return ticket, None

    @staticmethod
    def cancel_ticket(ticket_id):
        """Cancel a ticket"""
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return None, "Талон не найден"

        ticket.status = 'cancelled'
        ticket.completed_at = datetime.now(timezone.utc)

        if ticket.window_id:
            window = ServiceWindow.query.get(ticket.window_id)
            if window and window.current_ticket_id == ticket.id:
                window.current_ticket_id = None

        QueueService._recalculate_positions(ticket.service_id)
        db.session.commit()
        
        # Send Telegram Notification
        # TelegramService.notify_ticket_cancelled(ticket)
        
        return ticket, None

    @staticmethod
    def skip_ticket(ticket_id):
        """Skip a ticket (move to end of queue)"""
        ticket = Ticket.query.get(ticket_id)
        if not ticket or ticket.status != 'waiting':
            return None, "Талон не найден или уже обслуживается"

        # Move to end
        ticket.created_at = datetime.now(timezone.utc)
        ticket.status = 'waiting'

        if ticket.window_id:
            window = ServiceWindow.query.get(ticket.window_id)
            if window and window.current_ticket_id == ticket.id:
                window.current_ticket_id = None
            ticket.window_id = None

        QueueService._recalculate_positions(ticket.service_id)
        db.session.commit()
        return ticket, None

    @staticmethod
    def get_ticket_by_token(token):
        """Get ticket info by tracking token"""
        ticket = Ticket.query.filter_by(token=token).first()
        if not ticket:
            return None
        
        # Calculate estimated wait time
        if ticket.status == 'waiting':
            service = Service.query.get(ticket.service_id)
            estimated_wait = ticket.position * (service.estimated_time if service else 10)
        else:
            estimated_wait = 0

        result = ticket.to_dict()
        result['estimated_wait_minutes'] = estimated_wait
        return result

    @staticmethod
    def get_display_data():
        """Get data for display board"""
        windows = ServiceWindow.query.filter_by(is_active=True).all()
        waiting = Ticket.query.filter_by(status='waiting').order_by(Ticket.created_at.asc()).limit(10).all()
        
        return {
            'windows': [w.to_dict() for w in windows],
            'waiting': [t.to_dict() for t in waiting],
            'total_waiting': Ticket.query.filter_by(status='waiting').count()
        }

    @staticmethod
    def _recalculate_positions(service_id):
        """Recalculate positions for waiting tickets"""
        waiting_tickets = Ticket.query.filter_by(
            service_id=service_id,
            status='waiting'
        ).order_by(Ticket.created_at.asc()).all()
        
        for i, ticket in enumerate(waiting_tickets):
            ticket.position = i + 1
