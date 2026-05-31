import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.models import User, Roadmap, Progress, Goal, Quiz, Resume
from app.database import db
from app.services import GeminiService, CareerReadinessAnalyzer

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/lesson', methods=['POST'])
def get_or_generate_lesson():
    user = User.query.first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User profile not found.'}), 400
        
    data = request.get_json() or {}
    roadmap_id = data.get('roadmap_id')
    step_key = data.get('step_key')
    step_title = data.get('step_title')
    topics = data.get('topics', [])
    
    if not roadmap_id or not step_key or not step_title:
        return jsonify({'status': 'error', 'message': 'roadmap_id, step_key, and step_title are required'}), 400
        
    # Check if a progress record already exists with lesson content
    progress = Progress.query.filter_by(user_id=user.id, roadmap_id=roadmap_id, step_key=step_key).first()
    
    if progress and progress.lesson_content:
        try:
            lesson_data = json.loads(progress.lesson_content)
            return jsonify({
                'status': 'success',
                'data': lesson_data
            })
        except Exception:
            pass  # Fall back to regenerating if JSON parsing fails
            
    # Generate lesson content using Gemini
    gemini = GeminiService()
    generated_lesson = gemini.generate_lesson_for_node(step_title, topics)
    
    # Save/Update in DB
    if not progress:
        progress = Progress(
            user_id=user.id,
            roadmap_id=roadmap_id,
            step_key=step_key,
            is_completed=False,
            lesson_content=json.dumps(generated_lesson)
        )
        db.session.add(progress)
    else:
        progress.lesson_content = json.dumps(generated_lesson)
        
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': generated_lesson
    })

@progress_bp.route('/toggle', methods=['POST'])
def toggle_step_completion():
    user = User.query.first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User profile not found.'}), 400
        
    data = request.get_json() or {}
    roadmap_id = data.get('roadmap_id')
    step_key = data.get('step_key')
    completed = data.get('completed', True)
    
    if not roadmap_id or not step_key:
        return jsonify({'status': 'error', 'message': 'roadmap_id and step_key are required'}), 400
        
    progress = Progress.query.filter_by(user_id=user.id, roadmap_id=roadmap_id, step_key=step_key).first()
    
    if not progress:
        progress = Progress(
            user_id=user.id,
            roadmap_id=roadmap_id,
            step_key=step_key,
            is_completed=completed,
            completed_at=datetime.utcnow() if completed else None
        )
        db.session.add(progress)
    else:
        progress.is_completed = completed
        progress.completed_at = datetime.utcnow() if completed else None
        
    db.session.commit()
    
    # Re-calculate Career Readiness Score
    roadmap = Roadmap.query.filter_by(id=roadmap_id, user_id=user.id).first()
    new_score = user.readiness_score
    if roadmap:
        new_score = CareerReadinessAnalyzer.calculate_readiness_score(user.id, roadmap.goal_id)
        user.readiness_score = new_score
        db.session.commit()
        
    return jsonify({
        'status': 'success',
        'message': f"Step completion updated to {completed}",
        'data': {
            'step_key': step_key,
            'is_completed': completed,
            'new_readiness_score': new_score
        }
    })

@progress_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    user = User.query.first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User profile not found.'}), 400
        
    # Fetch active goal
    active_goal = Goal.query.filter_by(user_id=user.id, is_active=True).first()
    goal_title = active_goal.title if active_goal else None
    
    # Fetch latest resume details
    latest_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.uploaded_at.desc()).first()
    user_skills = []
    if latest_resume and latest_resume.extracted_skills:
        try:
            user_skills = json.loads(latest_resume.extracted_skills)
        except Exception:
            user_skills = []
            
    # Calculate matched/missing skills if goal active
    skills_matched = []
    skills_missing = []
    roadmap_progress = 0.0
    
    if active_goal:
        try:
            req_skills = json.loads(active_goal.required_skills)
        except Exception:
            req_skills = []
            
        user_skills_set = set(s.lower() for s in user_skills)
        skills_matched = [s for s in req_skills if s.lower() in user_skills_set]
        skills_missing = [s for s in req_skills if s.lower() not in user_skills_set]
        
        # Calculate roadmap progress
        roadmap = Roadmap.query.filter_by(user_id=user.id, goal_id=active_goal.id).first()
        if roadmap:
            try:
                steps_data = json.loads(roadmap.steps)
                steps_list = steps_data.get('roadmap', [])
            except Exception:
                steps_list = []
                
            total_steps = len(steps_list)
            if total_steps > 0:
                completed_steps = Progress.query.filter_by(
                    user_id=user.id, 
                    roadmap_id=roadmap.id, 
                    is_completed=True
                ).count()
                roadmap_progress = round((completed_steps / total_steps) * 100.0, 1)

    # Quiz history
    quizzes = Quiz.query.filter_by(user_id=user.id).filter(Quiz.score.isnot(None)).order_by(Quiz.completed_at.desc()).all()
    quiz_average = 0.0
    if quizzes:
        quiz_average = round(sum(q.score for q in quizzes) / len(quizzes), 1)

    return jsonify({
        'status': 'success',
        'data': {
            'user': user.to_dict(),
            'goal_title': goal_title,
            'skills_extracted_count': len(user_skills),
            'skills_matched_count': len(skills_matched),
            'skills_missing_count': len(skills_missing),
            'skills_matched': skills_matched,
            'skills_missing': skills_missing,
            'roadmap_progress': roadmap_progress,
            'quiz_average': quiz_average,
            'quizzes_taken': len(quizzes),
            'readiness_score': user.readiness_score
        }
    })
