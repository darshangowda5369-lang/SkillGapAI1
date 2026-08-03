import os
import json
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from app.models import User, Resume
from app.database import db
from app.services import PDFService, GeminiService
from app.routes.auth import get_authenticated_user

resume_bp = Blueprint('resume', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@resume_bp.route('/upload', methods=['POST'])
def upload_resume():
    # Make sure upload folder exists
    upload_dir = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in request'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected for uploading'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        try:
            # Extract text
            extracted_text = PDFService.extract_text(file_path)
            
            # Extract skills using Gemini
            gemini = GeminiService()
            extraction_result = gemini.extract_skills_from_resume(extracted_text)
            skills = extraction_result.get('skills', [])
            
            # Save to Database
            resume = Resume(
                user_id=user.id,
                filename=filename,
                raw_text=extracted_text,
                extracted_skills=json.dumps(skills)
            )
            db.session.add(resume)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Resume uploaded and analyzed successfully',
                'data': {
                    'resume_id': resume.id,
                    'filename': filename,
                    'extracted_skills': skills
                }
            })
            
        except ValueError as ve:
            # If PDF parsing failed locally (scanned PDF), try parsing directly with Gemini API
            _, ext = os.path.splitext(file_path.lower())
            if ext == '.pdf':
                try:
                    with open(file_path, 'rb') as f:
                        pdf_bytes = f.read()
                    
                    gemini = GeminiService()
                    extraction_result = gemini.extract_skills_from_pdf_bytes(pdf_bytes)
                    skills = extraction_result.get('skills', [])
                    
                    # Store a message in raw_text to denote it was a scanned PDF
                    extracted_text = "[Scanned PDF parsed via Gemini Vision OCR]"
                    
                    # Save to Database
                    resume = Resume(
                        user_id=user.id,
                        filename=filename,
                        raw_text=extracted_text,
                        extracted_skills=json.dumps(skills)
                    )
                    db.session.add(resume)
                    db.session.commit()
                    
                    return jsonify({
                        'status': 'success',
                        'message': 'Scanned PDF parsed successfully using Gemini OCR',
                        'data': {
                            'resume_id': resume.id,
                            'filename': filename,
                            'extracted_skills': skills
                        }
                    })
                except Exception as inner_e:
                    return jsonify({'status': 'error', 'message': f'Gemini OCR parsing failed: {str(inner_e)}'}), 400
            else:
                return jsonify({'status': 'error', 'message': str(ve)}), 400
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Failed to process resume: {str(e)}'}), 500
            
    else:
        return jsonify({'status': 'error', 'message': 'Allowed file types are pdf, docx, txt'}), 400

@resume_bp.route('/latest', methods=['GET'])
def get_latest_resume():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.uploaded_at.desc()).first()
    if not resume:
        return jsonify({
            'status': 'success',
            'data': None
        })
        
    return jsonify({
        'status': 'success',
        'data': resume.to_dict()
    })

@resume_bp.route('/demo-seed', methods=['POST'])
def seed_demo_resume():
    user = get_authenticated_user()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    profile_type = data.get('profile_type', 'frontend')
    
    profiles = {
        'frontend': {
            'filename': 'demo_frontend_resume.docx',
            'text': "Jane Smith\nFront-End Developer\nSkills: React, Redux, JavaScript, TypeScript, HTML5, CSS3, Tailwind CSS, Webpack, Jest, Git, responsive design, UI/UX optimization."
        },
        'devops': {
            'filename': 'demo_devops_resume.docx',
            'text': "Marcus Vance\nDevOps Engineer\nSkills: Docker, Kubernetes, AWS, Terraform, CI/CD pipelines, GitHub Actions, Linux, Bash, Prometheus, Grafana, Python, Ansible."
        },
        'data_science': {
            'filename': 'demo_data_science_resume.docx',
            'text': "Alice Kova\nData Scientist\nSkills: Python, SQL, Pandas, NumPy, Scikit-Learn, TensorFlow, PyTorch, Machine Learning, Tableau, Statistics, Jupyter Notebooks."
        }
    }
    
    profile = profiles.get(profile_type, profiles['frontend'])
    filename = profile['filename']
    extracted_text = profile['text']
    
    try:
        gemini = GeminiService()
        extraction_result = gemini.extract_skills_from_resume(extracted_text)
        skills = extraction_result.get('skills', [])
        
        # Save to Database
        resume = Resume(
            user_id=user.id,
            filename=filename,
            raw_text=extracted_text,
            extracted_skills=json.dumps(skills)
        )
        db.session.add(resume)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Demo {profile_type} resume seeded successfully',
            'data': {
                'resume_id': resume.id,
                'filename': filename,
                'extracted_skills': skills
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to seed demo resume: {str(e)}'}), 500
