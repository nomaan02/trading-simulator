"""
Configuration settings for German30 Trading Simulator
"""
import os
from datetime import time

class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data", "cache.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Trading Rules - CRITICAL PARAMETERS
    VALID_DAYS = ['Monday', 'Thursday', 'Friday']

    # Time windows in BST (GMT+1)
    TIME_WINDOWS = {
        'morning_1': {
            'label': '08:00 - 09:00 BST',
            'start': time(8, 0),
            'end': time(8, 59)
        },
        'morning_2': {
            'label': '09:00 - 10:00 BST',
            'start': time(9, 0),
            'end': time(9, 59)
        },
        'afternoon_1': {
            'label': '14:00 - 15:00 BST',
            'start': time(14, 0),
            'end': time(14, 59)
        },
        'afternoon_2': {
            'label': '15:00 - 16:00 BST',
            'start': time(15, 0),
            'end': time(15, 59)
        }
    }

    # Risk Management
    STOP_LOSS_POINTS = 18
    RISK_REWARD_RATIO = 3
    TAKE_PROFIT_POINTS = STOP_LOSS_POINTS * RISK_REWARD_RATIO  # 54 points

    # Data Configuration
    GERMAN30_SYMBOL = '^GDAXI'  # Yahoo Finance symbol for DAX
    BASE_TIMEFRAME = '1m'  # Fetch 1-minute data
    RESAMPLE_TIMEFRAME = '3min'  # Resample to 3-minute candles
    CACHE_EXPIRY_DAYS = 30

    # Supported timeframes for multi-timeframe analysis
    TIMEFRAMES = ['4h', '1h', '3m']

    # UI Configuration
    CHARTS_HEIGHT = {
        '4h': 250,
        '1h': 250,
        '3m': 400
    }

    # Replay Configuration
    DEFAULT_INITIAL_CANDLES = 5  # Number of candles to show initially
    REPLAY_SPEEDS = [1, 2, 5, 10]  # Available playback speeds

    # Risk Configuration (for position sizing)
    DEFAULT_RISK_AMOUNT = 100  # Default risk per trade in currency
    POINT_VALUE = 1  # Value per point movement (adjust based on contract size)

    # Session Configuration
    MAX_DATES_PER_SESSION = 50  # Maximum dates in a practice session

    # Timezone Configuration
    DATA_TIMEZONE = 'UTC'  # All data stored in UTC
    DISPLAY_TIMEZONE = 'Europe/London'  # BST/GMT for display
