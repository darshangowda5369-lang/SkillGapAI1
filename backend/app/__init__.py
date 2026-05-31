import os
from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.database import db

def create_app(config_class=Config):
    app = Flask(__name__)
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
