from flask import Blueprint, request, jsonify, render_template, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Resume
from app.ml.resume_analyzer import extract_text_from_pdf, analyze_resume
import os, json

resume_bp = Blueprint('resume', __name__, url_prefix='/resume')
ALLOWED_EXT = {'pdf'}
MAX_SIZE_BYTES = 5 * 1024 * 1024

@resume_bp.route('/')
@login_required
def index():
    past_resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).limit(5).all()
    return render_template('resume/upload.html', past_resumes=past_resumes)

@resume_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file component'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXT:
            return jsonify({'error': 'Invalid file type. Only PDF is allowed.'}), 400
            
        if request.content_length and request.content_length > MAX_SIZE_BYTES:
            return jsonify({'error': 'File size exceeds maximum limit (5MB).'}), 400
            
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/resumes')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, secure_filename(file.filename))
        file.save(filepath)
        
        text = extract_text_from_pdf(filepath)
        result = analyze_resume(text)
        
        r = Resume(
            user_id=current_user.id,
            filename=secure_filename(file.filename),
            score=result['score'],
            extracted_skills=json.dumps(result['matched_skills']),
            missing_skills=json.dumps(result['missing_skills']),
            suggestions=json.dumps(result['suggestions'])
        )
        db.session.add(r)
        db.session.commit()
        
        return jsonify({
            'score': r.score,
            'matched': result['matched_skills'],
            'missing': result['missing_skills'],
            'suggestions': result['suggestions'],
            'resume_id': r.id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resume_bp.route('/history')
@login_required
def history():
    resumes_db = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).all()
    resumes = []
    for r in resumes_db:
        resumes.append({
            'id': r.id,
            'uploaded_at': r.uploaded_at,
            'filename': r.filename,
            'score': r.score,
            'extracted_skills': json.loads(r.extracted_skills) if r.extracted_skills else [],
            'missing_skills': json.loads(r.missing_skills) if r.missing_skills else [],
            'suggestions': json.loads(r.suggestions) if r.suggestions else []
        })
    return render_template('resume/history.html', resumes=resumes)


@resume_bp.route('/<int:id>/detail')
@login_required
def detail(id):
    r = Resume.query.get(id)
    if not r or r.user_id != current_user.id:
        abort(404)
        
    return jsonify({
        'id': r.id,
        'filename': r.filename,
        'score': r.score,
        'extracted_skills': json.loads(r.extracted_skills) if r.extracted_skills else [],
        'missing_skills': json.loads(r.missing_skills) if r.missing_skills else [],
        'suggestions': json.loads(r.suggestions) if r.suggestions else [],
        'uploaded_at': r.uploaded_at.strftime('%d %b %Y, %I:%M %p')
    })
