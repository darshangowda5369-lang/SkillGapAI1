import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from sqlalchemy import inspect, text
from app.config import Config
from app.database import db


def _ensure_user_table_schema(app):
    with app.app_context():
        if db.engine.dialect.name != 'sqlite':
            return

        inspector = inspect(db.engine)
        if not inspector.has_table('users'):
            return

        existing_columns = {column['name'] for column in inspector.get_columns('users')}
        with db.engine.begin() as connection:
            if 'full_name' not in existing_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN full_name VARCHAR(120)'))
            if 'password_hash' not in existing_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)'))
            if 'session_token' not in existing_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN session_token VARCHAR(255)'))


def create_app(config_class=Config):
    # Resolve path to the frontend build output
    frontend_dist = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'frontend', 'dist'
    )

    app = Flask(__name__, static_folder=frontend_dist, static_url_path='')
    app.config.from_object(config_class)

    # In production, restrict CORS to the deployed Vercel frontend URL.
    # Set FRONTEND_URL env var on Render (e.g. https://skillgapai.vercel.app).
    # Locally, allow all origins for easy development.
    frontend_url = os.environ.get('FRONTEND_URL', '*')
    allowed_origins = frontend_url if frontend_url != '*' else '*'
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)
    
    # Initialize Database
    db.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.resume import resume_bp
    from app.routes.roadmap import roadmap_bp
    from app.routes.quiz import quiz_bp
    from app.routes.progress import progress_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(resume_bp, url_prefix='/api/resume')
    app.register_blueprint(roadmap_bp, url_prefix='/api/roadmap')
    app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')

    # ── Serve React frontend (SPA) ─────────────────────────────
    # In production / demo mode, serve the built React app.
    # All non-API routes fall through to index.html for client-side routing.
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        # If the requested file exists in dist/, serve it directly
        full_path = os.path.join(frontend_dist, path)
        if path and os.path.isfile(full_path):
            return send_from_directory(frontend_dist, path)
        # Otherwise return index.html (React handles routing)
        return send_from_directory(frontend_dist, 'index.html')
    
    # Create DB tables and normalize any legacy SQLite schema
    with app.app_context():
        db.create_all()
        _ensure_user_table_schema(app)

    return app

