"""
View routes for German30 Trading Simulator
"""
from flask import Blueprint, render_template
from models.session import Session
from models.trade import Trade

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    """Landing page"""
    # Get recent sessions
    recent_sessions = Session.query.order_by(Session.created_at.desc()).limit(5).all()

    # Get total stats across all sessions
    all_sessions = Session.query.all()
    total_trades = sum(s.total_trades for s in all_sessions)
    total_wins = sum(s.winning_trades for s in all_sessions)
    total_pnl = sum(s.total_pnl for s in all_sessions)

    overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0

    stats = {
        'total_sessions': len(all_sessions),
        'total_trades': total_trades,
        'overall_win_rate': round(overall_win_rate, 2),
        'total_pnl': round(total_pnl, 2)
    }

    return render_template(
        'index.html',
        recent_sessions=recent_sessions,
        stats=stats
    )


@views_bp.route('/simulator')
def simulator():
    """Main simulator interface"""
    return render_template('simulator.html')


@views_bp.route('/simulator/<int:session_id>')
def simulator_session(session_id):
    """Simulator with specific session loaded"""
    session = Session.query.get_or_404(session_id)
    return render_template('simulator.html', session=session)


@views_bp.route('/stats')
def stats():
    """Statistics dashboard - all sessions"""
    sessions = Session.query.order_by(Session.created_at.desc()).all()
    return render_template('stats.html', sessions=sessions)


@views_bp.route('/stats/<int:session_id>')
def session_stats(session_id):
    """Statistics dashboard for specific session"""
    session = Session.query.get_or_404(session_id)
    trades = Trade.query.filter_by(session_id=session_id).order_by(Trade.created_at).all()

    return render_template(
        'stats.html',
        session=session,
        trades=trades,
        single_session=True
    )
