import secrets
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.database import db

auth_bp = Blueprint('auth', __name__)


def get_authenticated_user():
    token = request.headers.get('Authorization', '')
    if token.startswith('Bearer '):
        token = token.split('Bearer ', 1)[1].strip()
    if not token:
        token = request.headers.get('X-Auth-Token', '')

    if not token:
        return None

    user = User.query.filter_by(session_token=token).first()
    if not user:
        return None
    return user


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    full_name = (data.get('full_name') or '').strip()
    username = (data.get('username') or '').strip().lower()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')

    if not full_name or not username or not email or not password:
        return jsonify({'status': 'error', 'message': 'Full name, username, email, and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'status': 'error', 'message': 'Username already exists'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'status': 'error', 'message': 'Email already exists'}), 409

    user = User(
        full_name=full_name,
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        readiness_score=0.0,
    )
    db.session.add(user)
    db.session.commit()

    token = secrets.token_urlsafe(24)
    user.session_token = token
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Account created successfully',
        'data': {
            'user': user.to_dict(),
            'token': token,
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

    if not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

    token = secrets.token_urlsafe(24)
    user.session_token = token
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'data': {
            'user': user.to_dict(),
            'token': token,
        }
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    user.session_token = None
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Logged out successfully'})


@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    return jsonify({
        'status': 'success',
        'data': user.to_dict()
    })


@auth_bp.route('/profile', methods=['POST'])
def update_profile():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json() or {}
    if 'username' in data:
        user.username = (data['username'] or '').strip().lower()
    if 'full_name' in data:
        user.full_name = (data['full_name'] or '').strip()
    if 'email' in data:
        user.email = (data['email'] or '').strip().lower()

    db.session.commit()
    return jsonify({
        'status': 'success',
        'data': user.to_dict()
    })
