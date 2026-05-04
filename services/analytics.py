from models import db, Ticket, DailyStats
from datetime import datetime, timezone, timedelta
from sqlalchemy import func


class AnalyticsService:
    """Analytics and reporting service"""

    @staticmethod
    def get_today_stats():
        """Get today's statistics"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_served = Ticket.query.filter(
            Ticket.status == 'completed',
            Ticket.completed_at >= today_start
        ).count()

        total_cancelled = Ticket.query.filter(
            Ticket.status == 'cancelled',
            Ticket.completed_at >= today_start
        ).count()

        total_waiting = Ticket.query.filter_by(status='waiting').count()
        total_serving = Ticket.query.filter(
            Ticket.status.in_(['called', 'serving'])
        ).count()

        # Average wait time today
        completed_tickets = Ticket.query.filter(
            Ticket.status == 'completed',
            Ticket.completed_at >= today_start,
            Ticket.called_at.isnot(None)
        ).all()

        avg_wait = 0
        avg_service = 0
        if completed_tickets:
            wait_times = [(t.called_at - t.created_at).total_seconds() / 60 for t in completed_tickets if t.called_at]
            service_times = [(t.completed_at - t.served_at).total_seconds() / 60 for t in completed_tickets if t.served_at and t.completed_at]
            avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0
            avg_service = sum(service_times) / len(service_times) if service_times else 0

        return {
            'total_served': total_served,
            'total_cancelled': total_cancelled,
            'total_waiting': total_waiting,
            'total_serving': total_serving,
            'avg_wait_time': round(avg_wait, 1),
            'avg_service_time': round(avg_service, 1),
            'total_today': total_served + total_cancelled
        }

    @staticmethod
    def get_hourly_distribution():
        """Get hourly distribution of tickets for today"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        tickets = Ticket.query.filter(
            Ticket.created_at >= today_start
        ).all()

        hours = {i: 0 for i in range(24)}
        for ticket in tickets:
            hour = ticket.created_at.hour
            hours[hour] += 1

        return {
            'labels': [f"{h:02d}:00" for h in range(24)],
            'data': [hours[h] for h in range(24)]
        }

    @staticmethod
    def get_service_distribution():
        """Get distribution of tickets by service type"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        results = db.session.query(
            Ticket.service_id,
            func.count(Ticket.id).label('count')
        ).filter(
            Ticket.created_at >= today_start
        ).group_by(Ticket.service_id).all()

        from models import Service
        labels = []
        data = []
        for service_id, count in results:
            service = Service.query.get(service_id)
            if service:
                labels.append(service.name)
                data.append(count)

        return {'labels': labels, 'data': data}

    @staticmethod
    def get_weekly_stats():
        """Get stats for the last 7 days"""
        labels = []
        served_data = []
        wait_data = []
        
        for i in range(6, -1, -1):
            day = datetime.now(timezone.utc) - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            served = Ticket.query.filter(
                Ticket.status == 'completed',
                Ticket.completed_at >= day_start,
                Ticket.completed_at < day_end
            ).count()
            
            completed = Ticket.query.filter(
                Ticket.status == 'completed',
                Ticket.completed_at >= day_start,
                Ticket.completed_at < day_end,
                Ticket.called_at.isnot(None)
            ).all()
            
            avg_wait = 0
            if completed:
                waits = [(t.called_at - t.created_at).total_seconds() / 60 for t in completed if t.called_at]
                avg_wait = sum(waits) / len(waits) if waits else 0

            day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            labels.append(day_names[day.weekday()])
            served_data.append(served)
            wait_data.append(round(avg_wait, 1))

        return {
            'labels': labels,
            'served': served_data,
            'avg_wait': wait_data
        }
