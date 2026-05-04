import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'queuesmart-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'queuesmart.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Queue settings
    MAX_QUEUE_SIZE = 100
    ESTIMATED_SERVICE_TIME_MINUTES = 10  # default per client
    
    # Admin credentials (in production use proper auth)
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
