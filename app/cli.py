import click
import os
from flask import Blueprint
from flask.cli import with_appcontext
from app.extensions import db
from app.models import Question
from sqlalchemy import func

cli_bp = Blueprint('cli', __name__, cli_group=None)

@cli_bp.cli.command('seed-questions')
@click.option('--file', 'csv_file', default=None,
              help='Path to specific CSV file to load.')
@click.option('--category', 'force_category', default=None,
              help='Force all loaded questions into this category.')
@with_appcontext
def seed_questions(csv_file, force_category):
    """
    Loads questions from one or more CSV files into the database.
    """
    from data.load_dataset import load_and_clean_questions_v2, validate_question
    ALLOWED_CATEGORIES = ['aptitude', 'coding', 'core', 'logical', 'numerical', 'verbal']
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    files_to_load = []
    if csv_file:
        files_to_load.append((csv_file, None))
    else:
        files_to_load = [
            (os.path.join(base_dir, 'data', 'aptitude_questions.csv'), None),
            (os.path.join(base_dir, 'data', 'coding_questions.csv'), 'coding'),
            (os.path.join(base_dir, 'data', 'core_questions.csv'), 'core')
        ]
        
    total_files_processed = 0
    total_inserted = 0
    total_skipped = 0
    total_failed = 0
    cat_counts = {c: 0 for c in ALLOWED_CATEGORIES}
    
    for fpath, default_cat in files_to_load:
        if not os.path.exists(fpath):
            click.echo(f"Warning: Skipping {fpath} - File not found.")
            continue
            
        click.echo(f"\nProcessing {fpath}...")
        try:
            data = load_and_clean_questions_v2(fpath, default_cat or 'aptitude')
            batch = []
            
            for row in data:
                if force_category and force_category in ALLOWED_CATEGORIES:
                    row['category'] = force_category
                    
                is_valid, reason = validate_question(row)
                if not is_valid:
                    total_failed += 1
                    continue
                    
                # Duplicate check
                exists = Question.query.filter(Question.question_text.ilike(row['question_text'])).first()
                if exists:
                    total_skipped += 1
                    continue
                    
                q = Question(**row)
                batch.append(q)
                total_inserted += 1
                cat_counts[row['category']] = cat_counts.get(row['category'], 0) + 1
                
                if len(batch) >= 100:
                    db.session.add_all(batch)
                    db.session.commit()
                    batch.clear()
                    
            if batch:
                db.session.add_all(batch)
                db.session.commit()
                
            total_files_processed += 1
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error processing {fpath}: {str(e)}")
            continue
            
    click.echo(f"\n===== FINAL SUMMARY =====")
    click.echo(f"Files processed: {total_files_processed}")
    click.echo(f"Total inserted: {total_inserted}")
    click.echo(f"Total skipped (duplicates): {total_skipped}")
    click.echo(f"Total failed (validation): {total_failed}")
    click.echo(f"Questions per category:")
    for c, count in cat_counts.items():
        if count > 0:
            click.echo(f"  {c}: {count}")

@cli_bp.cli.command('seed-coding')
@with_appcontext
def seed_coding():
    """
    Loads coding problems from data/coding_problems.json into the database.
    """
    import os, json
    import click
    from app.models import CodingProblem
    from app.extensions import db

    db.create_all()

    base_dir = os.path.dirname(os.path.dirname(__file__))
    json_file = os.path.join(base_dir, 'data', 'coding_problems.json')

    problems = []
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                problems = json.load(f)
        except Exception as e:
            click.echo(f"Warning: Error reading {json_file}: {e}")
    
    if not problems:
        click.echo("Warning: JSON missing or empty. Creating 10 sample problems inline.")
        problems = [
            {"title": "Two Sum", "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.", "difficulty": "Easy", "category": "Arrays", "input_format": "First line: array of integers. Second line: target integer.", "output_format": "List of two indices.", "constraints": "2 <= nums.length <= 10^4", "sample_input": "[2, 7, 11, 15]\n9", "sample_output": "[0, 1]", "explanation": "nums[0] + nums[1] == 9, return [0, 1]", "test_cases": [{"input": "[2,7,11,15]\n9", "expected_output": "[0, 1]"}]},
            {"title": "Palindrome Number", "description": "Given an integer x, return true if x is a palindrome, and false otherwise.", "difficulty": "Easy", "category": "Math", "input_format": "A single integer x.", "output_format": "true or false string.", "constraints": "-2^31 <= x <= 2^31 - 1", "sample_input": "121", "sample_output": "true", "explanation": "Reads the same forwards and backwards.", "test_cases": [{"input": "121", "expected_output": "true"}]},
            {"title": "Reverse Integer", "description": "Given a signed 32-bit integer x, return x with its digits reversed.", "difficulty": "Medium", "category": "Math", "input_format": "Integer", "output_format": "Integer", "constraints": "...", "sample_input": "123", "sample_output": "321", "explanation": "...", "test_cases": [{"input": "123", "expected_output": "321"}]},
            {"title": "Valid Parentheses", "description": "Determine if the input string is valid.", "difficulty": "Easy", "category": "Stacks", "input_format": "String", "output_format": "Boolean", "constraints": "...", "sample_input": "()", "sample_output": "true", "explanation": "...", "test_cases": [{"input": "()", "expected_output": "true"}]},
            {"title": "Maximum Subarray", "description": "Find the contiguous subarray with largest sum.", "difficulty": "Medium", "category": "Dynamic Programming", "input_format": "Array", "output_format": "Integer", "constraints": "...", "sample_input": "[-2,1,-3,4,-1,2,1,-5,4]", "sample_output": "6", "explanation": "...", "test_cases": [{"input": "[-2,1,-3,4,-1,2,1,-5,4]", "expected_output": "6"}]},
            {"title": "Climbing Stairs", "description": "How many distinct ways can you climb n steps?", "difficulty": "Easy", "category": "Dynamic Programming", "input_format": "Integer", "output_format": "Integer", "constraints": "...", "sample_input": "2", "sample_output": "2", "explanation": "...", "test_cases": [{"input": "2", "expected_output": "2"}]},
            {"title": "Merge String Alternately", "description": "Merge strings alternately.", "difficulty": "Easy", "category": "Strings", "input_format": "Two strings", "output_format": "String", "constraints": "...", "sample_input": "abc\npqr", "sample_output": "apbqcr", "explanation": "...", "test_cases": [{"input": "abc\npqr", "expected_output": "apbqcr"}]},
            {"title": "Single Number", "description": "Find the single element in array.", "difficulty": "Easy", "category": "Bit Manipulation", "input_format": "Array", "output_format": "Integer", "constraints": "...", "sample_input": "[2,2,1]", "sample_output": "1", "explanation": "...", "test_cases": [{"input": "[2,2,1]", "expected_output": "1"}]},
            {"title": "Contains Duplicate", "description": "Return true if duplicate exists.", "difficulty": "Easy", "category": "Arrays", "input_format": "Array", "output_format": "Boolean", "constraints": "...", "sample_input": "[1,2,3,1]", "sample_output": "true", "explanation": "...", "test_cases": [{"input": "[1,2,3,1]", "expected_output": "true"}]},
            {"title": "Container With Most Water", "description": "Find max water container.", "difficulty": "Medium", "category": "Greedy", "input_format": "Array", "output_format": "Integer", "constraints": "...", "sample_input": "[1,8,6,2,5,4,8,3,7]", "sample_output": "49", "explanation": "...", "test_cases": [{"input": "[1,8,6,2,5,4,8,3,7]", "expected_output": "49"}]}
        ]

    inserted = 0
    skipped = 0

    for p in problems:
        if CodingProblem.query.filter_by(title=p.get('title')).first():
            click.echo(f"Skipped (duplicate): {p.get('title')}")
            skipped += 1
            continue
        
        tc = p.get('test_cases', [])
        new_prob = CodingProblem(
            title=p.get('title'),
            description=p.get('description', ''),
            difficulty=p.get('difficulty', 'Easy'),
            category=p.get('category', 'Uncategorized'),
            input_format=p.get('input_format', ''),
            output_format=p.get('output_format', ''),
            constraints=p.get('constraints', ''),
            sample_input=p.get('sample_input', ''),
            sample_output=p.get('sample_output', ''),
            explanation=p.get('explanation', ''),
            test_cases=json.dumps(tc)
        )
        db.session.add(new_prob)
        inserted += 1
        click.echo(f"Inserted: {p.get('title')}")

    db.session.commit()
    click.echo(f"\nSeeding complete. {inserted} problems inserted, {skipped} skipped.")


@cli_bp.cli.command('seed-core')
@with_appcontext
def seed_core():
    """
    Shortcut: loads only data/core_questions.csv.
    Equivalent to: flask seed-questions --file data/core_questions.csv
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    csv_file = os.path.join(base_dir, 'data', 'core_questions.csv')
    os.system(f"flask seed-questions --file {csv_file}")


@cli_bp.cli.command('category-stats')
@with_appcontext
def category_stats():
    """
    Prints a formatted table to terminal:
    ┌──────────────┬──────┬────────┬────────┐
    ...
    """
    ALLOWED_CATEGORIES = ['aptitude', 'coding', 'core', 'logical', 'numerical', 'verbal']
    
    stats = {cat: {'easy': 0, 'medium': 0, 'hard': 0} for cat in ALLOWED_CATEGORIES}
    
    results = db.session.query(Question.category, Question.difficulty, func.count(Question.id)).group_by(Question.category, Question.difficulty).all()
    
    for cat, diff, count in results:
        if cat in stats and diff in stats[cat]:
            stats[cat][diff] = count
            
    click.echo("┌──────────────┬──────┬────────┬────────┐")
    click.echo("│ Category     │ Easy │ Medium │  Hard  │")
    click.echo("├──────────────┼──────┼────────┼────────┤")
    
    total_easy, total_med, total_hard = 0, 0, 0
    for cat in ALLOWED_CATEGORIES:
        e = stats[cat]['easy']
        m = stats[cat]['medium']
        h = stats[cat]['hard']
        total_easy += e
        total_med += m
        total_hard += h
        click.echo(f"│ {cat.ljust(12)} │ {str(e).center(4)} │ {str(m).center(6)} │ {str(h).center(6)} │")
        
    click.echo("├──────────────┼──────┼────────┼────────┤")
    click.echo(f"│ TOTAL        │ {str(total_easy).center(4)} │ {str(total_med).center(6)} │ {str(total_hard).center(6)} │")
    click.echo("└──────────────┴──────┴────────┴────────┘")


@cli_bp.cli.command('clear-questions')
@with_appcontext
def clear_questions():
    """
    Deletes all rows from the question table.
    """
    confirm = input("Are you sure? (yes/no): ")
    if confirm.strip().lower() == 'yes':
        try:
            count = db.session.query(Question).delete()
            db.session.commit()
            click.echo(f"Deleted {count} rows from Question table.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error clearing questions: {str(e)}")
    else:
        click.echo("Operation cancelled.")


@cli_bp.cli.command('question-stats')
@with_appcontext
def question_stats():
    """Legacy command, replaced mostly by category-stats"""
    total = Question.query.count()
    if total == 0:
        click.echo("No questions found in database.")
        return
        
    click.echo(f"\n--- Question Stats ---")
    click.echo(f"Total questions: {total}")
    click.echo("----------------------\n")

@cli_bp.cli.command('seed-data')
@with_appcontext
def seed_data():
    """Seed initial data like companies."""
    from app.models import Company
    
    companies = [
        {"name": "TCS", "domain": "service", "difficulty": "Easy", "avg_ctc_lpa": 3.5},
        {"name": "Infosys", "domain": "service", "difficulty": "Easy", "avg_ctc_lpa": 3.6},
        {"name": "Wipro", "domain": "service", "difficulty": "Easy", "avg_ctc_lpa": 3.4},
        {"name": "Accenture", "domain": "service", "difficulty": "Medium", "avg_ctc_lpa": 4.5},
        {"name": "Cognizant", "domain": "service", "difficulty": "Medium", "avg_ctc_lpa": 4.2},
        {"name": "HCL", "domain": "service", "difficulty": "Easy", "avg_ctc_lpa": 3.3},
        {"name": "Amazon", "domain": "product", "difficulty": "Hard", "avg_ctc_lpa": 18.0},
        {"name": "Google", "domain": "product", "difficulty": "Hard", "avg_ctc_lpa": 30.0},
        {"name": "Microsoft", "domain": "product", "difficulty": "Hard", "avg_ctc_lpa": 22.0},
        {"name": "Flipkart", "domain": "product", "difficulty": "Hard", "avg_ctc_lpa": 16.0}
    ]
    
    for c_data in companies:
        existing = Company.query.filter_by(name=c_data['name']).first()
        if not existing:
            company = Company(**c_data)
            db.session.add(company)
            
    db.session.commit()
    click.echo("Seeded 10 companies successfully.")
