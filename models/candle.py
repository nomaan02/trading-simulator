"""
Candle data model - stores historical price data
"""
from datetime import datetime
from models import db


class Candle(db.Model):
    """
    Represents a single candlestick (OHLCV data point)
    Caches German30 historical data locally
    """
    __tablename__ = 'candles'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Float, nullable=False)
    timeframe = db.Column(db.String(10), nullable=False, index=True)  # '1m', '3m', '1h', '4h'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite index for efficient querying
    __table_args__ = (
        db.Index('idx_timeframe_timestamp', 'timeframe', 'timestamp'),
    )

    def __repr__(self):
        return f'<Candle {self.timeframe} {self.timestamp} O:{self.open} H:{self.high} L:{self.low} C:{self.close}>'

    def to_dict(self):
        """Convert candle to dictionary format"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'time': int(self.timestamp.timestamp()),  # Unix timestamp for Lightweight Charts
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }

    @classmethod
    def from_series(cls, series, timeframe):
        """
        Create Candle instance from pandas Series

        Args:
            series: pandas Series with OHLCV data
            timeframe: timeframe string (e.g., '1m', '3m')

        Returns:
            Candle instance
        """
        return cls(
            timestamp=series.name.to_pydatetime() if hasattr(series.name, 'to_pydatetime') else series.name,
            open=float(series['Open']),
            high=float(series['High']),
            low=float(series['Low']),
            close=float(series['Close']),
            volume=float(series['Volume']),
            timeframe=timeframe
        )

    @classmethod
    def get_range(cls, start_date, end_date, timeframe):
        """
        Get candles for a date range and timeframe

        Args:
            start_date: Start datetime
            end_date: End datetime
            timeframe: Timeframe string

        Returns:
            List of Candle objects
        """
        return cls.query.filter(
            cls.timeframe == timeframe,
            cls.timestamp >= start_date,
            cls.timestamp <= end_date
        ).order_by(cls.timestamp).all()

    @classmethod
    def exists(cls, timestamp, timeframe):
        """Check if candle exists for given timestamp and timeframe"""
        return cls.query.filter_by(
            timestamp=timestamp,
            timeframe=timeframe
        ).first() is not None

    @classmethod
    def bulk_insert(cls, candles):
        """
        Bulk insert candles efficiently

        Args:
            candles: List of Candle objects
        """
        try:
            db.session.bulk_save_objects(candles)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error bulk inserting candles: {e}")
            return False
