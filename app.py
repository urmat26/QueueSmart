import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Service, ServiceWindow, User
import threading
from services.telegram_service import start_bot_polling

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Auth setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'page_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register API blueprint
from routes.api import api_bp
app.register_blueprint(api_bp)


# --- Page Routes ---

@app.route('/')
def page_index():
    return render_template('index.html')

@app.route('/client')
def page_client():
    return render_template('client.html')

@app.route('/admin')
@login_required
def page_admin():
    if not current_user.is_admin():
        flash('Доступ запрещён. Требуются права администратора.', 'error')
        return redirect(url_for('page_index'))
    return render_template('admin.html')

@app.route('/display')
def page_display():
    return render_template('display.html')

@app.route('/analytics')
@login_required
def page_analytics():
    if not current_user.is_admin():
        flash('Доступ запрещён.', 'error')
        return redirect(url_for('page_index'))
    return render_template('analytics.html')


# --- Auth Routes ---

@app.route('/login', methods=['GET', 'POST'])
def page_login():
    if current_user.is_authenticated:
        return redirect(url_for('page_index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('page_index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
            
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def page_register():
    if current_user.is_authenticated:
        return redirect(url_for('page_index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'error')
        else:
            user = User(username=username, email=email, role='client')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('page_login'))
            
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def page_logout():
    logout_user()
    return redirect(url_for('page_index'))

@app.route('/profile')
@login_required
def page_profile():
    # Show user's tickets in their personal cabinet
    from models import Ticket
    user_tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('profile.html', tickets=user_tickets)


# --- Socket.IO Events ---

@socketio.on('connect')
def handle_connect():
    print('[+] Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('[-] Client disconnected')

@socketio.on('queue_updated')
def handle_queue_update():
    emit('queue_update', broadcast=True)


# --- Initialize Database ---

def init_db():
    """Create tables and seed initial data"""
    with app.app_context():
        db.create_all()

        # Seed Admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@queuesmart.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('[OK] Admin user created')

        if Service.query.count() == 0:
            services = [
                Service(name='Obshchiy priyom', description='General questions', estimated_time=10, icon='📋'),
                Service(name='Finansy', description='Financial operations', estimated_time=15, icon='💰'),
                Service(name='Dokumenty', description='Document processing', estimated_time=20, icon='📄'),
                Service(name='VIP', description='Priority service', estimated_time=10, icon='⭐'),
            ]
            db.session.add_all(services)
            db.session.commit()
            print('[OK] Services seeded')

        if ServiceWindow.query.count() == 0:
            windows = [
                ServiceWindow(name='Window 1', operator_name='Operator 1'),
                ServiceWindow(name='Window 2', operator_name='Operator 2'),
                ServiceWindow(name='Window 3', operator_name='Operator 3'),
            ]
            db.session.add_all(windows)
            db.session.commit()
            print('[OK] Windows seeded')


if __name__ == '__main__':
    init_db()
    
    # Start Telegram Bot in background
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()

    print('\n' + '='*50)
    print('QueueSmart is running!')
    print('http://localhost:5000')
    print('='*50 + '\n')
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
