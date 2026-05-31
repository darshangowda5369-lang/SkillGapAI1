from flask import Blueprint, jsonify, request
from app.models import User
from app.database import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    # Fetch or create a default user for simplicity
    user = User.query.first()
    if not user:
        user = User(username="CyberLearner", email="learner@skillgap.ai", readiness_score=0.0)
        db.session.add(user)
        db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': user.to_dict()
    })

@auth_bp.route('/profile', methods=['POST'])
def update_profile():
    user = User.query.first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User profile not found'}), 404
        
    data = request.get_json() or {}
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
        
    db.session.commit()
    return jsonify({
        'status': 'success',
        'data': user.to_dict()
    })
