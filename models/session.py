"""
Session model - stores practice session information
"""
from datetime import datetime
from models import db
import json


class Session(db.Model):
    """
    Represents a practice trading session
    Contains multiple scenarios (dates) and tracks overall performance
    """
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Session configuration
    date_range_start = db.Column(db.Date, nullable=False)
    date_range_end = db.Column(db.Date, nullable=False)
    time_window = db.Column(db.String(20), nullable=False)  # 'morning_1', 'morning_2', etc.

    # Playlist of dates (stored as JSON array)
    playlist_json = db.Column(db.Text, nullable=False)  # ["2024-11-04", "2024-11-08", ...]
    current_date_index = db.Column(db.Integer, default=0)  # Current position in playlist

    # Session statistics
    total_trades = db.Column(db.Integer, default=0)
    winning_trades = db.Column(db.Integer, default=0)
    losing_trades = db.Column(db.Integer, default=0)
    scratch_trades = db.Column(db.Integer, default=0)  # Break-even trades
    total_pnl = db.Column(db.Float, default=0.0)  # Total P&L in points

    # Status
    is_completed = db.Column(db.Boolean, default=False)

    # Relationship to trades
    trades = db.relationship('Trade', backref='session', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Session {self.id} {self.time_window} {self.date_range_start} to {self.date_range_end}>'

    @property
    def playlist(self):
        """Get playlist as Python list"""
        return json.loads(self.playlist_json) if self.playlist_json else []

    @playlist.setter
    def playlist(self, dates_list):
        """Set playlist from Python list"""
        self.playlist_json = json.dumps(dates_list)

    @property
    def current_date(self):
        """Get current date from playlist"""
        playlist = self.playlist
        if 0 <= self.current_date_index < len(playlist):
            return playlist[self.current_date_index]
        return None

    @property
    def win_rate(self):
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def average_pnl(self):
        """Calculate average P&L per trade"""
        if self.total_trades == 0:
            return 0.0
        return self.total_pnl / self.total_trades

    @property
    def progress_percentage(self):
        """Calculate session progress percentage"""
        playlist = self.playlist
        if not playlist:
            return 0.0
        return (self.current_date_index / len(playlist)) * 100

    def advance_to_next_date(self):
        """Move to next date in playlist"""
        playlist = self.playlist
        if self.current_date_index < len(playlist) - 1:
            self.current_date_index += 1
            return True
        else:
            self.is_completed = True
            return False

    def update_statistics(self, trade):
        """
        Update session statistics after a trade

        Args:
            trade: Trade object
        """
        self.total_trades += 1

        if trade.outcome == 'win':
            self.winning_trades += 1
        elif trade.outcome == 'loss':
            self.losing_trades += 1
        elif trade.outcome == 'scratch':
            self.scratch_trades += 1

        self.total_pnl += trade.pnl_points
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'date_range_start': self.date_range_start.isoformat(),
            'date_range_end': self.date_range_end.isoformat(),
            'time_window': self.time_window,
            'playlist': self.playlist,
            'current_date_index': self.current_date_index,
            'current_date': self.current_date,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'scratch_trades': self.scratch_trades,
            'win_rate': round(self.win_rate, 2),
            'total_pnl': round(self.total_pnl, 2),
            'average_pnl': round(self.average_pnl, 2),
            'progress_percentage': round(self.progress_percentage, 2),
            'is_completed': self.is_completed
        }

    @classmethod
    def create_session(cls, date_range_start, date_range_end, time_window, dates_list):
        """
        Create a new practice session

        Args:
            date_range_start: Start date
            date_range_end: End date
            time_window: Time window key
            dates_list: List of date strings

        Returns:
            Session instance
        """
        session = cls(
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            time_window=time_window
        )
        session.playlist = dates_list
        return session
