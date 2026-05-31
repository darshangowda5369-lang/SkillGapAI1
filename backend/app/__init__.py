import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from app.config import Config
from app.database import db

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
    
    # Create DB tables and seed initial user
    with app.app_context():
        db.create_all()
        
        # Create a default user profile if none exists
        from app.models import User
        if not User.query.first():
            default_user = User(
                username="CyberLearner",
                email="learner@skillgap.ai",
                readiness_score=0.0
            )
            db.session.add(default_user)
            db.session.commit()
            print("Default user profile created successfully.")
            
    return app

