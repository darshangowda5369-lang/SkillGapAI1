import json
from flask import Blueprint, jsonify, request
from app.models import User, Resume, Goal, Roadmap
from app.database import db
from app.services import GeminiService, CareerReadinessAnalyzer
from app.routes.auth import get_authenticated_user

roadmap_bp = Blueprint('roadmap', __name__)

@roadmap_bp.route('/goals', methods=['GET'])
def get_goals():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
    user_goals = Goal.query.filter_by(user_id=user.id).order_by(Goal.created_at.desc()).all()
    presets = [
        {"title": "Frontend Engineer", "skills": ["HTML5", "CSS3", "JavaScript", "React", "Tailwind CSS", "TypeScript", "Git"]},
        {"title": "Backend Engineer", "skills": ["Python", "Flask", "SQL", "PostgreSQL", "REST APIs", "Docker", "Git", "Redis"]},
        {"title": "Data Scientist", "skills": ["Python", "SQL", "Pandas", "Scikit-Learn", "Machine Learning", "Jupyter", "Data Visualization"]},
        {"title": "DevOps Engineer", "skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS", "Terraform", "Git", "Bash"]}
    ]
    
    return jsonify({
        'status': 'success',
        'data': {
            'presets': presets,
            'user_goals': [g.to_dict() for g in user_goals]
        }
    })

@roadmap_bp.route('/generate', methods=['POST'])
def generate_roadmap():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    goal_title = data.get('goal_title')
    
    if not goal_title:
        return jsonify({'status': 'error', 'message': 'Goal title is required'}), 400

    # Get user's latest resume skills
    latest_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.uploaded_at.desc()).first()
    user_skills = []
    if latest_resume and latest_resume.extracted_skills:
        try:
            user_skills = json.loads(latest_resume.extracted_skills)
        except Exception:
            user_skills = []
            
    # Generate roadmap using Gemini
    gemini = GeminiService()
    analysis_result = gemini.generate_gap_analysis_and_roadmap(user_skills, goal_title)
    
    skills_missing = analysis_result.get('skills_missing', [])
    skills_matched = analysis_result.get('skills_matched', [])
    # Combined list forms required skills for the goal
    required_skills = list(set(skills_missing + skills_matched))
    
    # Disable previous active goals for this user
    Goal.query.filter_by(user_id=user.id, is_active=True).update({Goal.is_active: False})
    
    # Save the new goal
    goal = Goal(
        user_id=user.id,
        title=goal_title,
        required_skills=json.dumps(required_skills),
        is_active=True
    )
    db.session.add(goal)
    db.session.commit()
    
    # Save the roadmap
    roadmap = Roadmap(
        user_id=user.id,
        goal_id=goal.id,
        steps=json.dumps(analysis_result)
    )
    db.session.add(roadmap)
    db.session.commit()
    
    # Re-calculate readiness score
    new_score = CareerReadinessAnalyzer.calculate_readiness_score(user.id, goal.id)
    user.readiness_score = new_score
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Roadmap generated and analysis complete',
        'data': {
            'goal_id': goal.id,
            'roadmap_id': roadmap.id,
            'readiness_score': new_score,
            'skills_matched': skills_matched,
            'skills_missing': skills_missing,
            'roadmap': analysis_result.get('roadmap', [])
        }
    })

@roadmap_bp.route('/active', methods=['GET'])
def get_active_roadmap():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
    active_goal = Goal.query.filter_by(user_id=user.id, is_active=True).first()
    if not active_goal:
        return jsonify({
            'status': 'success',
            'data': None
        })
        
    roadmap = Roadmap.query.filter_by(user_id=user.id, goal_id=active_goal.id).first()
    if not roadmap:
        return jsonify({
            'status': 'success',
            'data': None
        })
        
    # Re-calculate score on load to keep it fresh
    new_score = CareerReadinessAnalyzer.calculate_readiness_score(user.id, active_goal.id)
    if user.readiness_score != new_score:
        user.readiness_score = new_score
        db.session.commit()
        
    # Fetch matching/missing skills
    latest_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.uploaded_at.desc()).first()
    user_skills = []
    if latest_resume and latest_resume.extracted_skills:
        try:
            user_skills = json.loads(latest_resume.extracted_skills)
        except Exception:
            user_skills = []
            
    user_skills_set = set(s.lower() for s in user_skills)
    
    try:
        req_skills = json.loads(active_goal.required_skills)
    except Exception:
        req_skills = []
        
    skills_matched = [s for s in req_skills if s.lower() in user_skills_set]
    skills_missing = [s for s in req_skills if s.lower() not in user_skills_set]
    
    # Load completed progress steps
    from app.models import Progress
    progress_records = Progress.query.filter_by(user_id=user.id, roadmap_id=roadmap.id).all()
    completed_steps = {p.step_key: p.is_completed for p in progress_records if p.is_completed}
    
    roadmap_dict = roadmap.to_dict()
    # Inject completed flag into roadmap steps
    if 'steps' in roadmap_dict and 'roadmap' in roadmap_dict['steps']:
        for step in roadmap_dict['steps']['roadmap']:
            step['completed'] = completed_steps.get(step.get('step_key'), False)

    return jsonify({
        'status': 'success',
        'data': {
            'goal_id': active_goal.id,
            'goal_title': active_goal.title,
            'readiness_score': user.readiness_score,
            'skills_matched': skills_matched,
            'skills_missing': skills_missing,
            'roadmap': roadmap_dict['steps'].get('roadmap', []),
            'roadmap_id': roadmap.id
        }
    })
