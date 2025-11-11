"""
Database models initialization
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)

    with app.app_context():
        # Import all models here to ensure they're registered
        from models import candle, session, trade

        # Create tables
        db.create_all()

        print("Database initialized successfully!")

# Import models for easy access
from models.candle import Candle
from models.session import Session
from models.trade import Trade

__all__ = ['db', 'init_db', 'Candle', 'Session', 'Trade']
