from flask import render_template, request, jsonify, current_app, flash
from flask_login import login_required, current_user
import json
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import CodingProblem, Submission
from app.coding import coding_bp
from app.coding.executor import run_code

@coding_bp.route('/')
def coding_list():
    try:
        difficulty = request.args.get('difficulty', '')
        category = request.args.get('category', '')
        
        query = CodingProblem.query
        
        if difficulty and difficulty != 'All Difficulties':
            query = query.filter_by(difficulty=difficulty)
        if category and category != 'All Categories':
            query = query.filter_by(category=category)
            
        problems = query.all()
        
        # Determine available filters dynamically
        difficulties = db.session.query(CodingProblem.difficulty).distinct().all()
        categories = db.session.query(CodingProblem.category).distinct().all()
        
        diff_list = [d[0] for d in difficulties]
        cat_list = [c[0] for c in categories]
        
        # global stats
        total_problems = CodingProblem.query.count()
        easy_count = CodingProblem.query.filter_by(difficulty='Easy').count()
        med_count = CodingProblem.query.filter_by(difficulty='Medium').count()
        hard_count = CodingProblem.query.filter_by(difficulty='Hard').count()
        
        return render_template('coding/coding_list.html', 
                               problems=problems,
                               diff_filters=diff_list,
                               cat_filters=cat_list,
                               selected_diff=difficulty,
                               selected_cat=category,
                               total_problems=total_problems,
                               easy_count=easy_count,
                               med_count=med_count,
                               hard_count=hard_count)
    except SQLAlchemyError as e:
        current_app.logger.error(f"DB Error coding list: {e}")
        flash("Could not load coding problems. Database might not be initialized.", "danger")
        return render_template('coding/coding_list.html', problems=[], diff_filters=[], cat_filters=[])
    except Exception as e:
        current_app.logger.error(f"Coding List Error: {e}")
        flash("An unexpected error occurred.", "danger")
        return render_template('coding/coding_list.html', problems=[], diff_filters=[], cat_filters=[])


@coding_bp.route('/<int:problem_id>')
def coding_detail(problem_id):
    problem = CodingProblem.query.get_or_404(problem_id)
    
    submissions = []
    if current_user.is_authenticated:
        submissions = Submission.query.filter_by(user_id=current_user.id, problem_id=problem.id)\
            .order_by(Submission.created_at.desc()).limit(5).all()
            
    return render_template('coding/coding_detail.html', problem=problem, submissions=submissions)


@coding_bp.route('/run', methods=['POST'])
def run():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    problem_id = data.get('problem_id')
    code = data.get('code')
    
    if not problem_id or not code:
        return jsonify({"error": "Missing problem_id or code"}), 400
        
    problem = CodingProblem.query.get(problem_id)
    if not problem:
        return jsonify({"error": "Problem not found"}), 404
        
    sample_input = problem.sample_input
    expected_output = problem.sample_output
    
    result = run_code(code, sample_input, expected_output=expected_output)
    result['expected'] = expected_output
    
    return jsonify(result)


@coding_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    problem_id = data.get('problem_id')
    code = data.get('code')
    
    if not problem_id or not code:
        return jsonify({"error": "Missing problem_id or code"}), 400
        
    problem = CodingProblem.query.get(problem_id)
    if not problem:
        return jsonify({"error": "Problem not found"}), 404
        
    # Parse test cases
    try:
        test_cases = json.loads(problem.test_cases) if problem.test_cases else []
    except Exception as e:
        current_app.logger.error(f"Error parsing test cases for problem {problem_id}: {e}")
        return jsonify({"error": "Invalid test cases schema on server."}), 500
        
    passed_count = 0
    total = len(test_cases)
    details = []
    total_time = 0.0
    
    overall_result = 'passed' if total > 0 else 'error'
    first_error_msg = ""
    
    for tc in test_cases:
        inp = tc.get('input', '')
        exp = tc.get('expected_output', '')
        
        res = run_code(code, inp, expected_output=exp)
        total_time += res.get('execution_time', 0.0)
        
        tc_passed = (res.get('status') == 'passed')
        if tc_passed:
            passed_count += 1
        elif res.get('status') == 'error':
             overall_result = 'error'
             tc_passed = False
             if not first_error_msg:
                 first_error_msg = res.get('error', 'Execution Error')
        else:
             overall_result = 'failed'
             tc_passed = False
        
        details.append({
            "input": inp,
            "expected": exp,
            "actual": res.get('output', ''),
            "passed": tc_passed,
            "error_message": res.get('error')
        })
        
        # Stop short circuit on first explicit process crash or syntax error
        if res.get('status') == 'error':
             break
             
    if overall_result != 'error' and passed_count < total:
        overall_result = 'failed'
        
    submission = Submission(
        user_id=current_user.id,
        problem_id=problem.id,
        code=code,
        language='python',
        result=overall_result,
        execution_time=round(total_time, 4),
        error_message=first_error_msg
    )
    db.session.add(submission)
    db.session.commit()
    
    current_app.logger.info(f"User {current_user.id} submitted code for problem {problem.id} resulting in {overall_result}")
    
    return jsonify({
        "result": overall_result,
        "passed": passed_count,
        "total": total,
        "details": details,
        "execution_time": round(total_time, 4),
        "error": first_error_msg
    })
