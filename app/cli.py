import click
import os
from flask import Blueprint
from flask.cli import with_appcontext
from app.extensions import db
from app.models import Question
from sqlalchemy import func

cli_bp = Blueprint('cli', __name__, cli_group=None)

@cli_bp.cli.command('seed-questions')
@with_appcontext
def seed_questions():
    """
    Reads data/aptitude_questions.csv using load_and_clean_questions(),
    validates each row with validate_question(),
    inserts into DB skipping duplicates (check by question_text),
    prints final count: inserted / skipped / failed with reasons.
    Wraps everything in a try/except — on any fatal error, 
    rolls back and prints the error clearly.
    """
    from data.load_dataset import load_and_clean_questions, validate_question
    
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'aptitude_questions.csv')
    if not os.path.exists(csv_path):
        click.echo(f"Error: Could not find CSV at {csv_path}")
        return

    try:
        data = load_and_clean_questions(csv_path)
        
        inserted = 0
        skipped = 0
        failed = 0
        failure_reasons = {}
        
        batch = []
        batch_size = 100
        
        for row in data:
            is_valid, reason = validate_question(row)
            if not is_valid:
                failed += 1
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                continue
                
            # Check for duplicate
            exists = Question.query.filter_by(question_text=row['question_text']).first()
            if exists:
                skipped += 1
                continue
                
            q = Question(**row)
            batch.append(q)
            inserted += 1
            
            if len(batch) >= batch_size:
                db.session.add_all(batch)
                db.session.commit()
                batch = []
                
        # Insert remaining
        if batch:
            db.session.add_all(batch)
            db.session.commit()
            
        click.echo(f"\nFinal Count:")
        click.echo(f"Inserted: {inserted}")
        click.echo(f"Skipped (duplicates): {skipped}")
        click.echo(f"Failed (validation error): {failed}")
        if failure_reasons:
            click.echo("Failure reasons:")
            for reason, count in failure_reasons.items():
                click.echo(f"  - {reason}: {count}")

    except Exception as e:
        db.session.rollback()
        click.echo(f"Fatal error during seeding: {str(e)}")


@cli_bp.cli.command('clear-questions')
@with_appcontext
def clear_questions():
    """
    Deletes all rows from the question table.
    Asks for confirmation: 'Are you sure? (yes/no): '
    Only proceeds if user types 'yes'.
    Prints count of deleted rows.
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
    """
    Prints a summary table to terminal:
    - Total questions in DB
    - Count per category
    - Count per difficulty
    - Count per category+difficulty combination
    Uses only SQLAlchemy queries, no pandas.
    """
    total = Question.query.count()
    if total == 0:
        click.echo("No questions found in database.")
        return
        
    click.echo(f"\n--- Question Stats ---")
    click.echo(f"Total questions: {total}")
    
    click.echo(f"\nCount per category:")
    cats = db.session.query(Question.category, func.count(Question.id)).group_by(Question.category).all()
    for cat, count in cats:
        click.echo(f"  {cat}: {count}")
        
    click.echo(f"\nCount per difficulty:")
    diffs = db.session.query(Question.difficulty, func.count(Question.id)).group_by(Question.difficulty).all()
    for diff, count in diffs:
        click.echo(f"  {diff}: {count}")
        
    click.echo(f"\nCount per category+difficulty:")
    combos = db.session.query(Question.category, Question.difficulty, func.count(Question.id)).group_by(Question.category, Question.difficulty).all()
    for cat, diff, count in combos:
        click.echo(f"  {cat} - {diff}: {count}")
    click.echo("----------------------\n")
