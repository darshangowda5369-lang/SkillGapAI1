import json
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.models import User, Quiz, Goal
from app.database import db
from app.services import GeminiService, CareerReadinessAnalyzer

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/generate', methods=['POST'])
def generate_quiz():
    user = User.query.first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User profile not found.'}), 400
        
    data = request.get_json() or {}
    skill_name = data.get('skill_name')
    if not skill_name:
        return jsonify({'status': 'error', 'message': 'Skill name is required'}), 400
        
    gemini = GeminiService()
    quiz_data = gemini.generate_quiz_for_skill(skill_name)
    
    # Save the generated quiz (without score initially)
    quiz = Quiz(
        user_id=user.id,
        skill_name=skill_name,
        questions=json.dumps(quiz_data.get('questions', []))
    )
    db.session.add(quiz)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': {
            'quiz_id': quiz.id,
            'skill_name': skill_name,
            'questions': quiz_data.get('questions', [])
        }
    })

@quiz_bp.route('/submit', methods=['POST'])
def submit_quiz():
    user = User.query.first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User profile not found.'}), 400
        
    data = request.get_json() or {}
    quiz_id = data.get('quiz_id')
    user_answers = data.get('answers')  # Dictionary of {question_id: answer_choice}
    
    if not quiz_id or user_answers is None:
        return jsonify({'status': 'error', 'message': 'Quiz ID and answers are required'}), 400
        
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=user.id).first()
    if not quiz:
        return jsonify({'status': 'error', 'message': 'Quiz not found'}), 404
        
    try:
        questions = json.loads(quiz.questions)
    except Exception:
        return jsonify({'status': 'error', 'message': 'Failed to load quiz questions'}), 500
        
    # Evaluate answers
    correct_count = 0
    total_questions = len(questions)
    results = []
    
    for q in questions:
        q_id = str(q.get('id'))
        correct_ans = q.get('correct_answer')
        user_ans = user_answers.get(q_id)
        
        is_correct = (user_ans == correct_ans)
        if is_correct:
            correct_count += 1
            
        results.append({
            'id': q.get('id'),
            'question': q.get('question'),
            'options': q.get('options'),
            'correct_answer': correct_ans,
            'user_answer': user_ans,
            'is_correct': is_correct,
            'explanation': q.get('explanation')
        })
        
    score_percentage = (correct_count / total_questions) * 100.0 if total_questions > 0 else 0.0
    
    # Update quiz entry in DB
    quiz.score = score_percentage
    quiz.completed_at = datetime.utcnow()
    db.session.commit()
    
    # Recalculate Career Readiness Score if there is an active goal
    active_goal = Goal.query.filter_by(user_id=user.id, is_active=True).first()
    if active_goal:
        new_score = CareerReadinessAnalyzer.calculate_readiness_score(user.id, active_goal.id)
        user.readiness_score = new_score
        db.session.commit()
        
    return jsonify({
        'status': 'success',
        'data': {
            'quiz_id': quiz.id,
            'skill_name': quiz.skill_name,
            'score': score_percentage,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'results': results,
            'new_readiness_score': user.readiness_score
        }
    })

@quiz_bp.route('/history', methods=['GET'])
def get_quiz_history():
    user = User.query.first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User profile not found.'}), 400
        
    quizzes = Quiz.query.filter_by(user_id=user.id).filter(Quiz.score.isnot(None)).order_by(Quiz.completed_at.desc()).all()
    return jsonify({
        'status': 'success',
        'data': [q.to_dict() for q in quizzes]
    })
