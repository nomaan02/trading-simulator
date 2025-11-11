"""
Trade model - stores individual trade records
"""
from datetime import datetime
from models import db
import json


class Trade(db.Model):
    """
    Represents a single trade within a practice session
    Stores entry, exit, and outcome information
    """
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Trade timing
    entry_timestamp = db.Column(db.DateTime, nullable=False)
    exit_timestamp = db.Column(db.DateTime)

    # Trade details
    direction = db.Column(db.String(10), nullable=False)  # 'long' or 'short'
    entry_price = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float, nullable=False)
    take_profit = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float)

    # Outcome
    outcome = db.Column(db.String(10))  # 'win', 'loss', 'scratch', or None if not resolved
    pnl_points = db.Column(db.Float, default=0.0)  # P&L in points
    pnl_percentage = db.Column(db.Float, default=0.0)  # P&L as percentage of risk

    # Trade quality
    is_a_grade = db.Column(db.Boolean, default=False)  # Did it meet all A-grade criteria?
    notes = db.Column(db.Text)  # User's observations

    # Chart annotations (drawings, labels, etc.)
    annotations_json = db.Column(db.Text)  # Stored as JSON

    def __repr__(self):
        return f'<Trade {self.id} {self.direction} @ {self.entry_price} - {self.outcome}>'

    @property
    def annotations(self):
        """Get annotations as Python object"""
        return json.loads(self.annotations_json) if self.annotations_json else {}

    @annotations.setter
    def annotations(self, data):
        """Set annotations from Python object"""
        self.annotations_json = json.dumps(data) if data else None

    @property
    def duration_minutes(self):
        """Calculate trade duration in minutes"""
        if self.exit_timestamp and self.entry_timestamp:
            delta = self.exit_timestamp - self.entry_timestamp
            return delta.total_seconds() / 60
        return None

    @property
    def risk_reward_ratio(self):
        """Calculate actual risk-reward ratio achieved"""
        if self.outcome == 'win':
            return abs(self.pnl_points / (self.entry_price - self.stop_loss if self.direction == 'long'
                                          else self.stop_loss - self.entry_price))
        elif self.outcome == 'loss':
            return -1.0
        return 0.0

    def calculate_sl_tp(self, stop_loss_points, risk_reward_ratio):
        """
        Calculate stop loss and take profit based on entry

        Args:
            stop_loss_points: Fixed stop loss distance in points
            risk_reward_ratio: Target risk-reward ratio
        """
        take_profit_points = stop_loss_points * risk_reward_ratio

        if self.direction == 'long':
            self.stop_loss = self.entry_price - stop_loss_points
            self.take_profit = self.entry_price + take_profit_points
        elif self.direction == 'short':
            self.stop_loss = self.entry_price + stop_loss_points
            self.take_profit = self.entry_price - take_profit_points

    def determine_outcome(self, candles):
        """
        Determine trade outcome by analyzing subsequent candles

        Args:
            candles: List of Candle objects after entry

        Returns:
            dict with outcome details
        """
        for candle in candles:
            if self.direction == 'long':
                # Check if SL hit
                if candle.low <= self.stop_loss:
                    self.outcome = 'loss'
                    self.exit_price = self.stop_loss
                    self.exit_timestamp = candle.timestamp
                    self.pnl_points = self.exit_price - self.entry_price
                    self.pnl_percentage = (self.pnl_points / (self.entry_price - self.stop_loss)) * 100
                    return {
                        'outcome': 'loss',
                        'exit_price': self.exit_price,
                        'exit_timestamp': self.exit_timestamp.isoformat(),
                        'pnl_points': round(self.pnl_points, 2)
                    }

                # Check if TP hit
                if candle.high >= self.take_profit:
                    self.outcome = 'win'
                    self.exit_price = self.take_profit
                    self.exit_timestamp = candle.timestamp
                    self.pnl_points = self.exit_price - self.entry_price
                    self.pnl_percentage = (self.pnl_points / (self.entry_price - self.stop_loss)) * 100
                    return {
                        'outcome': 'win',
                        'exit_price': self.exit_price,
                        'exit_timestamp': self.exit_timestamp.isoformat(),
                        'pnl_points': round(self.pnl_points, 2)
                    }

            elif self.direction == 'short':
                # Check if SL hit
                if candle.high >= self.stop_loss:
                    self.outcome = 'loss'
                    self.exit_price = self.stop_loss
                    self.exit_timestamp = candle.timestamp
                    self.pnl_points = self.entry_price - self.exit_price
                    self.pnl_percentage = (self.pnl_points / (self.stop_loss - self.entry_price)) * 100
                    return {
                        'outcome': 'loss',
                        'exit_price': self.exit_price,
                        'exit_timestamp': self.exit_timestamp.isoformat(),
                        'pnl_points': round(self.pnl_points, 2)
                    }

                # Check if TP hit
                if candle.low <= self.take_profit:
                    self.outcome = 'win'
                    self.exit_price = self.take_profit
                    self.exit_timestamp = candle.timestamp
                    self.pnl_points = self.entry_price - self.exit_price
                    self.pnl_percentage = (self.pnl_points / (self.stop_loss - self.entry_price)) * 100
                    return {
                        'outcome': 'win',
                        'exit_price': self.exit_price,
                        'exit_timestamp': self.exit_timestamp.isoformat(),
                        'pnl_points': round(self.pnl_points, 2)
                    }

        # No outcome yet - trade still open
        return {'outcome': 'pending'}

    def to_dict(self):
        """Convert trade to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'entry_timestamp': self.entry_timestamp.isoformat(),
            'exit_timestamp': self.exit_timestamp.isoformat() if self.exit_timestamp else None,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'exit_price': self.exit_price,
            'outcome': self.outcome,
            'pnl_points': round(self.pnl_points, 2),
            'pnl_percentage': round(self.pnl_percentage, 2),
            'duration_minutes': self.duration_minutes,
            'risk_reward_ratio': round(self.risk_reward_ratio, 2) if self.risk_reward_ratio else None,
            'is_a_grade': self.is_a_grade,
            'notes': self.notes,
            'annotations': self.annotations
        }

    @classmethod
    def create_trade(cls, session_id, timestamp, direction, entry_price, stop_loss_points, risk_reward_ratio, notes=None, annotations=None):
        """
        Create a new trade

        Args:
            session_id: Parent session ID
            timestamp: Entry timestamp
            direction: 'long' or 'short'
            entry_price: Entry price
            stop_loss_points: SL distance in points
            risk_reward_ratio: RR ratio
            notes: Optional notes
            annotations: Optional annotations dict

        Returns:
            Trade instance
        """
        trade = cls(
            session_id=session_id,
            entry_timestamp=timestamp,
            direction=direction,
            entry_price=entry_price,
            notes=notes
        )

        # Calculate SL and TP
        trade.calculate_sl_tp(stop_loss_points, risk_reward_ratio)

        # Set annotations if provided
        if annotations:
            trade.annotations = annotations

        return trade
