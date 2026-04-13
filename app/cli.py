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
    Shortcut: loads only data/coding_questions.csv.
    Equivalent to: flask seed-questions --file data/coding_questions.csv
    """
    from flask.cli import run_command
    import sys
    base_dir = os.path.dirname(os.path.dirname(__file__))
    csv_file = os.path.join(base_dir, 'data', 'coding_questions.csv')
    os.system(f"flask seed-questions --file {csv_file}")


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
