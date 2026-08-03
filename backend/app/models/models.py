from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    session_token = db.Column(db.String(255), unique=True, nullable=True)
    readiness_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    resumes = db.relationship('Resume', backref='user', lazy=True, cascade="all, delete-orphan")
    goals = db.relationship('Goal', backref='user', lazy=True, cascade="all, delete-orphan")
    roadmaps = db.relationship('Roadmap', backref='user', lazy=True, cascade="all, delete-orphan")
    quizzes = db.relationship('Quiz', backref='user', lazy=True, cascade="all, delete-orphan")
    progress_records = db.relationship('Progress', backref='user', lazy=True, cascade="all, delete-orphan")
    certificates = db.relationship('Certificate', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'username': self.username,
            'email': self.email,
            'readiness_score': self.readiness_score,
            'created_at': self.created_at.isoformat()
        }

class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    extracted_skills = db.Column(db.Text, nullable=True)  # JSON list of strings
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        try:
            skills = json.loads(self.extracted_skills) if self.extracted_skills else []
        except Exception:
            skills = []
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'extracted_skills': skills,
            'uploaded_at': self.uploaded_at.isoformat()
        }

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    required_skills = db.Column(db.Text, nullable=False)  # JSON list of strings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        import json
        try:
            req_skills = json.loads(self.required_skills) if self.required_skills else []
        except Exception:
            req_skills = []
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'required_skills': req_skills,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

class Roadmap(db.Model):
    __tablename__ = 'roadmaps'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    steps = db.Column(db.Text, nullable=False)  # JSON representation of roadmap nodes/milestones
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    goal = db.relationship('Goal', backref=db.backref('roadmaps', lazy=True))

    def to_dict(self):
        import json
        try:
            steps_data = json.loads(self.steps) if self.steps else {}
        except Exception:
            steps_data = {}
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'goal_title': self.goal.title if self.goal else 'Unknown',
            'steps': steps_data,
            'created_at': self.created_at.isoformat()
        }

class Progress(db.Model):
    __tablename__ = 'progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    roadmap_id = db.Column(db.Integer, db.ForeignKey('roadmaps.id'), nullable=False)
    step_key = db.Column(db.String(100), nullable=False)  # references step identifier in roadmap
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    lesson_content = db.Column(db.Text, nullable=True)  # cached generated lesson notes

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'roadmap_id': self.roadmap_id,
            'step_key': self.step_key,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'has_lesson': self.lesson_content is not None
        }

class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    certificate_id = db.Column(db.String(120), unique=True, nullable=False)
    goal_title = db.Column(db.String(150), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'certificate_id': self.certificate_id,
            'goal_title': self.goal_title,
            'file_name': self.file_name,
            'download_path': self.file_path,
            'issued_at': self.issued_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # JSON representation of questions
    score = db.Column(db.Float, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        try:
            questions_data = json.loads(self.questions) if self.questions else []
        except Exception:
            questions_data = []
        return {
            'id': self.id,
            'user_id': self.user_id,
            'skill_name': self.skill_name,
            'questions': questions_data,
            'score': self.score,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat()
        }
