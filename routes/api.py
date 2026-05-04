from flask import Blueprint, jsonify, request
from models import db, Service, ServiceWindow, Ticket
from services.queue_service import QueueService
from services.analytics import AnalyticsService

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ─── Queue Operations ───────────────────────────────────────────

@api_bp.route('/tickets', methods=['POST'])
def create_ticket():
    """Register a new client in the queue"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400

    client_name = data.get('client_name', '').strip()
    client_phone = data.get('client_phone', '').strip()
    service_id = data.get('service_id')

    if not client_name or not service_id:
        return jsonify({'error': 'Имя клиента и услуга обязательны'}), 400

    ticket, error = QueueService.create_ticket(client_name, client_phone, service_id)
    if error:
        return jsonify({'error': error}), 400

    # Link to logged in user if exists
    from flask_login import current_user
    if current_user.is_authenticated:
        from models import db
        ticket.user_id = current_user.id
        db.session.commit()

    return jsonify({
        'success': True,
        'ticket': ticket.to_dict(),
        'token': ticket.token,
        'message': f'Ваш номер: {ticket.ticket_number}'
    }), 201


@api_bp.route('/tickets/<token>', methods=['GET'])
def get_ticket_status(token):
    """Check ticket status by token"""
    result = QueueService.get_ticket_by_token(token)
    if not result:
        return jsonify({'error': 'Талон не найден'}), 404
    return jsonify(result)


@api_bp.route('/queue', methods=['GET'])
def get_queue():
    """Get current queue status"""
    service_id = request.args.get('service_id', type=int)
    status = QueueService.get_queue_status(service_id)
    return jsonify(status)


@api_bp.route('/queue/call-next', methods=['POST'])
def call_next():
    """Call the next client"""
    data = request.get_json()
    window_id = data.get('window_id')
    service_id = data.get('service_id')

    if not window_id:
        return jsonify({'error': 'Укажите окно обслуживания'}), 400

    ticket, error = QueueService.call_next(window_id, service_id)
    if error:
        return jsonify({'error': error}), 400

    return jsonify({
        'success': True,
        'ticket': ticket.to_dict()
    })


@api_bp.route('/tickets/<int:ticket_id>/serve', methods=['POST'])
def start_serve(ticket_id):
    """Start serving a client"""
    ticket, error = QueueService.start_serving(ticket_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'success': True, 'ticket': ticket.to_dict()})


@api_bp.route('/tickets/<int:ticket_id>/complete', methods=['POST'])
def complete_ticket(ticket_id):
    """Complete serving a client"""
    ticket, error = QueueService.complete_ticket(ticket_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'success': True, 'ticket': ticket.to_dict()})


@api_bp.route('/tickets/<int:ticket_id>/link-telegram', methods=['POST'])
def link_telegram(ticket_id):
    """Link telegram chat ID to ticket"""
    data = request.get_json()
    chat_id = data.get('chat_id')
    if not chat_id:
        return jsonify({'error': 'chat_id обязателен'}), 400
    
    success, error = QueueService.link_telegram(ticket_id, chat_id)
    if error:
        return jsonify({'error': error}), 400
        
    return jsonify({'success': True})


@api_bp.route('/tickets/<int:ticket_id>/cancel', methods=['POST'])
def cancel_ticket(ticket_id):
    """Cancel a ticket"""
    ticket, error = QueueService.cancel_ticket(ticket_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'success': True, 'ticket': ticket.to_dict()})


@api_bp.route('/tickets/<int:ticket_id>/skip', methods=['POST'])
def skip_ticket(ticket_id):
    """Skip a ticket"""
    ticket, error = QueueService.skip_ticket(ticket_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'success': True, 'ticket': ticket.to_dict()})


# ─── Services ───────────────────────────────────────────────────

@api_bp.route('/services', methods=['GET'])
def get_services():
    """Get all available services"""
    services = Service.query.filter_by(is_active=True).all()
    return jsonify([s.to_dict() for s in services])


@api_bp.route('/services', methods=['POST'])
def create_service():
    """Create a new service"""
    data = request.get_json()
    service = Service(
        name=data.get('name', 'Новая услуга'),
        description=data.get('description', ''),
        estimated_time=data.get('estimated_time', 10),
        icon=data.get('icon', '📋')
    )
    db.session.add(service)
    db.session.commit()
    return jsonify({'success': True, 'service': service.to_dict()}), 201


@api_bp.route('/services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    """Delete a service"""
    service = Service.query.get_or_404(service_id)
    service.is_active = False
    db.session.commit()
    return jsonify({'success': True})


# ─── Windows ────────────────────────────────────────────────────

@api_bp.route('/windows', methods=['GET'])
def get_windows():
    """Get all service windows"""
    windows = ServiceWindow.query.all()
    return jsonify([w.to_dict() for w in windows])


@api_bp.route('/windows', methods=['POST'])
def create_window():
    """Create a new service window"""
    data = request.get_json()
    window = ServiceWindow(
        name=data.get('name', 'Новое окно'),
        operator_name=data.get('operator_name', 'Оператор')
    )
    db.session.add(window)
    db.session.commit()
    return jsonify({'success': True, 'window': window.to_dict()}), 201


@api_bp.route('/windows/<int:window_id>/toggle', methods=['POST'])
def toggle_window(window_id):
    """Toggle window active status"""
    window = ServiceWindow.query.get_or_404(window_id)
    window.is_active = not window.is_active
    db.session.commit()
    return jsonify({'success': True, 'window': window.to_dict()})


# ─── Display ────────────────────────────────────────────────────

@api_bp.route('/display', methods=['GET'])
def get_display():
    """Get data for display board"""
    return jsonify(QueueService.get_display_data())


# ─── Analytics ──────────────────────────────────────────────────

@api_bp.route('/analytics/today', methods=['GET'])
def get_today_analytics():
    """Get today's analytics"""
    return jsonify(AnalyticsService.get_today_stats())


@api_bp.route('/analytics/hourly', methods=['GET'])
def get_hourly():
    """Get hourly distribution"""
    return jsonify(AnalyticsService.get_hourly_distribution())


@api_bp.route('/analytics/services', methods=['GET'])
def get_service_stats():
    """Get service distribution"""
    return jsonify(AnalyticsService.get_service_distribution())


@api_bp.route('/analytics/weekly', methods=['GET'])
def get_weekly():
    """Get weekly stats"""
    return jsonify(AnalyticsService.get_weekly_stats())
