"""
German30 Trading Strategy Simulator - Main Flask Application
"""
from flask import Flask
from flask_cors import CORS
from config import Config
from models import init_db
import os


def create_app(config_class=Config):
    """Application factory pattern"""

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for API endpoints
    CORS(app)

    # Ensure data directory exists
    os.makedirs(os.path.join(app.config['BASE_DIR'], 'data'), exist_ok=True)

    # Initialize database
    init_db(app)

    # Register blueprints
    from routes.views import views_bp
    from routes.api import api_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Context processor to inject config into templates
    @app.context_processor
    def inject_config():
        # Convert time objects to JSON-serializable format
        time_windows_serializable = {}
        for key, window in Config.TIME_WINDOWS.items():
            time_windows_serializable[key] = {
                'label': window['label'],
                'start': window['start'].strftime('%H:%M'),
                'end': window['end'].strftime('%H:%M')
            }

        return {
            'config': Config,
            'time_windows': time_windows_serializable
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

    return app


if __name__ == '__main__':
    app = create_app()

    print("=" * 60)
    print("German30 Trading Strategy Simulator")
    print("=" * 60)
    print(f"Server starting on http://localhost:5000")
    print(f"Press CTRL+C to quit")
    print("=" * 60)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
