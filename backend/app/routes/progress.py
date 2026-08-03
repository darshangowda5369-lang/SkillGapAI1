import json
import os
from datetime import datetime
from flask import Blueprint, jsonify, request, send_from_directory, current_app
from app.models import User, Roadmap, Progress, Goal, Quiz, Resume, Certificate
from app.database import db
from app.services import GeminiService, CareerReadinessAnalyzer, CertificateService, calculate_roadmap_completion_percentage
from app.routes.auth import get_authenticated_user

progress_bp = Blueprint('progress', __name__)


def _ensure_certificate_for_completion(user, goal_title, roadmap):
    if not roadmap:
        return None

    certificate = Certificate.query.filter_by(user_id=user.id, goal_title=goal_title).order_by(Certificate.issued_at.desc()).first()
    if certificate:
        return certificate

    total_steps = 0
    try:
        steps_data = json.loads(roadmap.steps)
        total_steps = len(steps_data.get('roadmap', []))
    except Exception:
        total_steps = 0

    completed_steps = Progress.query.filter_by(user_id=user.id, roadmap_id=roadmap.id, is_completed=True).count()
    if total_steps <= 0 or completed_steps < total_steps:
        return None

    certificate_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'certificates')
    cert_data = CertificateService.generate_certificate_pdf(user, goal_title, certificate_dir)
    cert_record = Certificate(
        user_id=user.id,
        certificate_id=cert_data['certificate_id'],
        goal_title=goal_title,
        file_name=cert_data['file_name'],
        file_path=cert_data['download_path'],
        completed_at=datetime.utcnow(),
    )
    db.session.add(cert_record)
    db.session.commit()
    return cert_record


@progress_bp.route('/lesson', methods=['POST'])
def get_or_generate_lesson():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json() or {}
    roadmap_id = data.get('roadmap_id')
    step_key = data.get('step_key')
    step_title = data.get('step_title')
    topics = data.get('topics', [])

    if not roadmap_id or not step_key or not step_title:
        return jsonify({'status': 'error', 'message': 'roadmap_id, step_key, and step_title are required'}), 400

    progress = Progress.query.filter_by(user_id=user.id, roadmap_id=roadmap_id, step_key=step_key).first()

    if progress and progress.lesson_content:
        try:
            lesson_data = json.loads(progress.lesson_content)
            return jsonify({
                'status': 'success',
                'data': lesson_data
            })
        except Exception:
            pass

    gemini = GeminiService()
    generated_lesson = gemini.generate_lesson_for_node(step_title, topics)

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
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

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

    roadmap = Roadmap.query.filter_by(id=roadmap_id, user_id=user.id).first()
    active_goal = Goal.query.filter_by(user_id=user.id, is_active=True).first()
    new_score = user.readiness_score
    certificate_download_url = None
    certificate_id = None
    roadmap_progress = 0.0

    if roadmap:
        new_score = CareerReadinessAnalyzer.calculate_readiness_score(user.id, roadmap.goal_id)
        user.readiness_score = new_score
        db.session.commit()

        try:
            steps_data = json.loads(roadmap.steps)
            steps_list = steps_data.get('roadmap', [])
        except Exception:
            steps_list = []

        total_steps = len(steps_list)
        completed_steps = Progress.query.filter_by(user_id=user.id, roadmap_id=roadmap.id, is_completed=True).count()
        roadmap_progress = calculate_roadmap_completion_percentage(total_steps, completed_steps)

        if roadmap_progress >= 100.0 and active_goal:
            cert_record = _ensure_certificate_for_completion(user, active_goal.title, roadmap)
            if cert_record:
                certificate_download_url = f'/api/progress/certificate/download/{cert_record.id}'
                certificate_id = cert_record.certificate_id

    return jsonify({
        'status': 'success',
        'message': f"Step completion updated to {completed}",
        'data': {
            'step_key': step_key,
            'is_completed': completed,
            'new_readiness_score': new_score,
            'roadmap_progress': roadmap_progress,
            'certificate_download_url': certificate_download_url,
            'certificate_id': certificate_id,
        }
    })


@progress_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    active_goal = Goal.query.filter_by(user_id=user.id, is_active=True).first()
    goal_title = active_goal.title if active_goal else None

    latest_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.uploaded_at.desc()).first()
    user_skills = []
    if latest_resume and latest_resume.extracted_skills:
        try:
            user_skills = json.loads(latest_resume.extracted_skills)
        except Exception:
            user_skills = []

    skills_matched = []
    skills_missing = []
    roadmap_progress = 0.0
    certificate_download_url = None
    certificate_id = None

    if active_goal:
        try:
            req_skills = json.loads(active_goal.required_skills)
        except Exception:
            req_skills = []

        user_skills_set = set(s.lower() for s in user_skills)
        skills_matched = [s for s in req_skills if s.lower() in user_skills_set]
        skills_missing = [s for s in req_skills if s.lower() not in user_skills_set]

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
                roadmap_progress = calculate_roadmap_completion_percentage(total_steps, completed_steps)

            if roadmap_progress >= 100.0:
                certificate = _ensure_certificate_for_completion(user, active_goal.title, roadmap)
                if certificate:
                    certificate_download_url = f'/api/progress/certificate/download/{certificate.id}'
                    certificate_id = certificate.certificate_id

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
            'readiness_score': user.readiness_score,
            'certificate_download_url': certificate_download_url,
            'certificate_id': certificate_id,
        }
    })


@progress_bp.route('/certificate/download/<int:certificate_id>', methods=['GET'])
def download_certificate(certificate_id):
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    certificate = Certificate.query.filter_by(id=certificate_id, user_id=user.id).first()
    if not certificate:
        return jsonify({'status': 'error', 'message': 'Certificate not found'}), 404

    directory = os.path.dirname(certificate.file_path)
    filename = os.path.basename(certificate.file_path)
    return send_from_directory(directory, filename, as_attachment=True)

