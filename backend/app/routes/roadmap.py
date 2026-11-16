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
        {"title": "Full-Stack Developer", "skills": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Node.js", "Express", "SQL", "REST APIs", "Git"]},
        {"title": "Software Tester", "skills": ["Testing Frameworks", "Test Automation", "Python", "JavaScript", "Selenium", "Git", "Bug Tracking"]},
        {"title": "Cybersecurity Engineer", "skills": ["Networking", "Linux", "Security Fundamentals", "Cryptography", "Penetration Testing", "Incident Response"]},
        {"title": "Machine Learning Engineer", "skills": ["Python", "Statistics", "Pandas", "Machine Learning", "Scikit-Learn", "Model Evaluation", "MLOps"]},
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
    goal_title = (data.get('goal_title') or '').strip()
    
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
    required_skills = GeminiService.get_role_required_skills(goal_title, user_skills)
    
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
        
    # Reconcile legacy saved goals with the selected role's full requirements.
    latest_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.uploaded_at.desc()).first()
    user_skills = []
    if latest_resume and latest_resume.extracted_skills:
        try:
            user_skills = json.loads(latest_resume.extracted_skills)
        except Exception:
            user_skills = []

    req_skills = GeminiService.get_role_required_skills(active_goal.title, user_skills)
    try:
        stored_required_skills = json.loads(active_goal.required_skills) if active_goal.required_skills else []
    except (TypeError, ValueError):
        stored_required_skills = []
    if stored_required_skills != req_skills:
        active_goal.required_skills = json.dumps(req_skills)
        db.session.commit()

    skills_matched = [
        required for required in req_skills
        if any(GeminiService.skills_match(required, current) for current in user_skills)
    ]
    skills_missing = [
        required for required in req_skills
        if not any(GeminiService.skills_match(required, current) for current in user_skills)
    ]

    # Re-calculate score on load to keep it fresh using the normalized role baseline.
    new_score = CareerReadinessAnalyzer.calculate_readiness_score(user.id, active_goal.id)
    if user.readiness_score != new_score:
        user.readiness_score = new_score
        db.session.commit()
    
    # Load completed progress steps
    from app.models import Progress
    progress_records = Progress.query.filter_by(user_id=user.id, roadmap_id=roadmap.id).all()
    completed_steps = {p.step_key: p.is_completed for p in progress_records if p.is_completed}
    
    roadmap_dict = roadmap.to_dict()
    original_steps = []
    if isinstance(roadmap_dict.get('steps'), dict):
        original_steps = roadmap_dict['steps'].get('roadmap', [])
    if not isinstance(original_steps, list):
        original_steps = []
    completed_skills = []
    for step in original_steps:
        if not isinstance(step, dict) or step.get('step_key') not in completed_steps:
            continue
        covered_skills = step.get('skills_covered', [])
        if isinstance(covered_skills, str):
            covered_skills = [covered_skills]
        completed_skills.extend(skill for skill in covered_skills if isinstance(skill, str))
    if isinstance(roadmap_dict.get('steps'), dict):
        aligned = GeminiService._align_roadmap_to_gaps(
            roadmap_dict['steps'], active_goal.title, skills_matched, skills_missing, user_skills
        )
        roadmap_dict['steps'] = GeminiService._sanitize_roadmap_result(aligned)
    # Inject completed flag into roadmap steps
    if 'steps' in roadmap_dict and 'roadmap' in roadmap_dict['steps']:
        for step in roadmap_dict['steps']['roadmap']:
            step['completed'] = completed_steps.get(step.get('step_key'), False) or any(
                GeminiService.skills_match(skill, completed_skill)
                for skill in step.get('skills_covered', [])
                for completed_skill in completed_skills
            )

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
