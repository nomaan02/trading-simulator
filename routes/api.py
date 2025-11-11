"""
API routes for German30 Trading Simulator
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from config import Config
from models import db
from models.session import Session
from models.trade import Trade
from models.candle import Candle
from data.processor import DataProcessor
from data.fetcher import DataFetcher

api_bp = Blueprint('api', __name__)


@api_bp.route('/available-dates', methods=['GET'])
def get_available_dates():
    """
    Get list of valid trading dates in range

    Query params:
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - time_window: Time window key (optional)

    Returns:
        List of available dates with metadata
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        time_window = request.args.get('time_window')

        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date required'}), 400

        processor = DataProcessor()

        if time_window:
            sessions = processor.get_available_sessions(start_date, end_date, time_window)
            return jsonify({
                'success': True,
                'count': len(sessions),
                'sessions': sessions
            })
        else:
            dates = processor.get_available_dates(start_date, end_date)
            dates_list = [d.isoformat() for d in dates]
            return jsonify({
                'success': True,
                'count': len(dates_list),
                'dates': dates_list
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/session/start', methods=['POST'])
def start_session():
    """
    Create a new practice session

    JSON body:
        - dates: Array of date strings
        - time_window: Time window key
        - date_range_start: Start date (optional, for metadata)
        - date_range_end: End date (optional, for metadata)

    Returns:
        Session object with ID
    """
    try:
        data = request.get_json()

        dates = data.get('dates', [])
        time_window = data.get('time_window')

        if not dates or not time_window:
            return jsonify({'error': 'dates and time_window required'}), 400

        if time_window not in Config.TIME_WINDOWS:
            return jsonify({'error': f'Invalid time_window: {time_window}'}), 400

        if len(dates) > Config.MAX_DATES_PER_SESSION:
            return jsonify({
                'error': f'Maximum {Config.MAX_DATES_PER_SESSION} dates allowed per session'
            }), 400

        # Determine date range
        date_objs = [datetime.strptime(d, '%Y-%m-%d').date() for d in dates]
        date_range_start = min(date_objs)
        date_range_end = max(date_objs)

        # Create session
        session = Session.create_session(
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            time_window=time_window,
            dates_list=dates
        )

        db.session.add(session)
        db.session.commit()

        return jsonify({
            'success': True,
            'session': session.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/session/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details"""
    try:
        session = Session.query.get(session_id)

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        return jsonify({
            'success': True,
            'session': session.to_dict()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/session/<int:session_id>/next', methods=['POST'])
def next_scenario(session_id):
    """
    Advance to next date in session playlist

    Returns:
        Next scenario metadata
    """
    try:
        session = Session.query.get(session_id)

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        # Advance to next date
        has_next = session.advance_to_next_date()
        db.session.commit()

        if not has_next:
            return jsonify({
                'success': True,
                'completed': True,
                'message': 'Session completed!',
                'session': session.to_dict()
            })

        # Get metadata for new current date
        processor = DataProcessor()
        metadata = processor.get_scenario_metadata(session.current_date, session.time_window)

        return jsonify({
            'success': True,
            'completed': False,
            'scenario': metadata,
            'session': session.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/candles', methods=['GET'])
def get_candles():
    """
    Get candle data for replay

    Query params:
        - session_id: Session ID
        - date: Date (YYYY-MM-DD)
        - time_window: Time window key
        - timeframe: Timeframe ('3m', '1h', '4h')
        - limit: Number of candles to reveal (optional)

    Returns:
        Candle data array
    """
    try:
        session_id = request.args.get('session_id', type=int)
        date_str = request.args.get('date')
        time_window = request.args.get('time_window')
        timeframe = request.args.get('timeframe', '3m')
        limit = request.args.get('limit', type=int)

        if not date_str or not time_window:
            return jsonify({'error': 'date and time_window required'}), 400

        processor = DataProcessor()
        fetcher = DataFetcher()

        # Prepare data for this scenario
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        multiframe_data = processor.prepare_replay_data(date, time_window, timeframes=[timeframe])

        df = multiframe_data.get(timeframe)

        if df is None or df.empty:
            return jsonify({
                'success': True,
                'candles': [],
                'total': 0
            })

        # Convert to dictionary format
        candles = []
        for timestamp, row in df.iterrows():
            candles.append({
                'time': int(timestamp.timestamp()),
                'timestamp': timestamp.isoformat(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row['Volume'])
            })

        # Apply limit if specified
        if limit and limit > 0:
            candles = candles[:limit]

        return jsonify({
            'success': True,
            'candles': candles,
            'total': len(candles),
            'timeframe': timeframe
        })

    except Exception as e:
        import traceback
        print(f"Error in get_candles: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/trade/enter', methods=['POST'])
def enter_trade():
    """
    Enter a new trade

    JSON body:
        - session_id: Session ID
        - timestamp: Entry timestamp (ISO format)
        - direction: 'long' or 'short'
        - entry_price: Entry price
        - notes: Optional notes
        - annotations: Optional annotations object
        - is_a_grade: Optional boolean

    Returns:
        Trade object with calculated SL/TP
    """
    try:
        data = request.get_json()

        session_id = data.get('session_id')
        timestamp_str = data.get('timestamp')
        direction = data.get('direction')
        entry_price = data.get('entry_price')
        notes = data.get('notes')
        annotations = data.get('annotations')
        is_a_grade = data.get('is_a_grade', False)

        # Validation
        if not all([session_id, timestamp_str, direction, entry_price]):
            return jsonify({
                'error': 'session_id, timestamp, direction, and entry_price required'
            }), 400

        if direction not in ['long', 'short']:
            return jsonify({'error': 'direction must be "long" or "short"'}), 400

        # Verify session exists
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        # Parse timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

        # Create trade
        trade = Trade.create_trade(
            session_id=session_id,
            timestamp=timestamp,
            direction=direction,
            entry_price=float(entry_price),
            stop_loss_points=Config.STOP_LOSS_POINTS,
            risk_reward_ratio=Config.RISK_REWARD_RATIO,
            notes=notes,
            annotations=annotations
        )

        trade.is_a_grade = is_a_grade

        db.session.add(trade)
        db.session.commit()

        return jsonify({
            'success': True,
            'trade': trade.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/trade/<int:trade_id>/outcome', methods=['GET'])
def get_trade_outcome(trade_id):
    """
    Determine and return trade outcome

    Query params:
        - date: Date of the trade (YYYY-MM-DD)
        - time_window: Time window key

    Returns:
        Trade outcome with exit details
    """
    try:
        trade = Trade.query.get(trade_id)

        if not trade:
            return jsonify({'error': 'Trade not found'}), 404

        # If outcome already determined, return it
        if trade.outcome:
            return jsonify({
                'success': True,
                'trade': trade.to_dict()
            })

        # Get required params
        date_str = request.args.get('date')
        time_window = request.args.get('time_window')

        if not date_str or not time_window:
            return jsonify({'error': 'date and time_window required'}), 400

        # Get candles after entry
        processor = DataProcessor()
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        multiframe_data = processor.prepare_replay_data(date, time_window, timeframes=['3m'])
        df = multiframe_data.get('3m')

        if df is None or df.empty:
            return jsonify({'error': 'No candle data available'}), 404

        # Filter candles after entry timestamp
        candles_after = []
        for timestamp, row in df.iterrows():
            # Ensure trade.entry_timestamp is timezone-aware for comparison
            entry_ts = trade.entry_timestamp
            if entry_ts.tzinfo is None:
                import pytz
                entry_ts = pytz.UTC.localize(entry_ts)

            if timestamp > entry_ts:
                candle = Candle.from_series(row, '3m')
                candle.timestamp = timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp
                candles_after.append(candle)

        if not candles_after:
            return jsonify({
                'success': True,
                'outcome': 'pending',
                'message': 'Trade still open - no subsequent candles'
            })

        # Determine outcome
        outcome_result = trade.determine_outcome(candles_after)

        # Update session statistics if outcome determined
        if trade.outcome:
            session = trade.session
            session.update_statistics(trade)

        db.session.commit()

        return jsonify({
            'success': True,
            'trade': trade.to_dict(),
            'outcome_details': outcome_result
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/session/<int:session_id>/stats', methods=['GET'])
def get_session_stats(session_id):
    """
    Get comprehensive statistics for a session

    Returns:
        Session stats with trade details
    """
    try:
        session = Session.query.get(session_id)

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        # Get all trades for this session
        trades = Trade.query.filter_by(session_id=session_id).order_by(Trade.created_at).all()

        # Calculate additional stats
        trades_by_outcome = {
            'win': [t for t in trades if t.outcome == 'win'],
            'loss': [t for t in trades if t.outcome == 'loss'],
            'scratch': [t for t in trades if t.outcome == 'scratch']
        }

        # Win/loss by direction
        long_trades = [t for t in trades if t.direction == 'long']
        short_trades = [t for t in trades if t.direction == 'short']

        # A-grade setups
        a_grade_trades = [t for t in trades if t.is_a_grade]
        a_grade_wins = [t for t in a_grade_trades if t.outcome == 'win']

        stats = {
            'session': session.to_dict(),
            'total_trades': len(trades),
            'by_outcome': {
                'wins': len(trades_by_outcome['win']),
                'losses': len(trades_by_outcome['loss']),
                'scratches': len(trades_by_outcome['scratch'])
            },
            'by_direction': {
                'long': len(long_trades),
                'short': len(short_trades),
                'long_win_rate': (len([t for t in long_trades if t.outcome == 'win']) / len(long_trades) * 100)
                if long_trades else 0,
                'short_win_rate': (len([t for t in short_trades if t.outcome == 'win']) / len(short_trades) * 100)
                if short_trades else 0
            },
            'a_grade_setups': {
                'total': len(a_grade_trades),
                'wins': len(a_grade_wins),
                'win_rate': (len(a_grade_wins) / len(a_grade_trades) * 100) if a_grade_trades else 0
            },
            'pnl': {
                'total': session.total_pnl,
                'average': session.average_pnl,
                'best_trade': max([t.pnl_points for t in trades], default=0),
                'worst_trade': min([t.pnl_points for t in trades], default=0)
            },
            'recent_trades': [t.to_dict() for t in trades[-10:]]  # Last 10 trades
        }

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/session/<int:session_id>/trades', methods=['GET'])
def get_session_trades(session_id):
    """Get all trades for a session"""
    try:
        session = Session.query.get(session_id)

        if not session:
            return jsonify({'error': 'Session not found'}), 404

        trades = Trade.query.filter_by(session_id=session_id).order_by(Trade.created_at).all()

        return jsonify({
            'success': True,
            'count': len(trades),
            'trades': [t.to_dict() for t in trades]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/time-windows', methods=['GET'])
def get_time_windows():
    """Get all available time windows"""
    try:
        windows = []
        for key, window in Config.TIME_WINDOWS.items():
            windows.append({
                'key': key,
                'label': window['label'],
                'start': window['start'].strftime('%H:%M'),
                'end': window['end'].strftime('%H:%M')
            })

        return jsonify({
            'success': True,
            'time_windows': windows
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'German30 Trading Simulator',
        'version': '1.0.0'
    })
