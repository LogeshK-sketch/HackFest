"""
Shared utility functions for Smart Placement Preparation
& Guidance System.
Import from here to avoid circular imports between blueprints.
"""

from app.models import TestAttempt

def get_category_score(user_id: int, category: str) -> int:
    """
    Calculates the rolling average score for a user in a given
    category based on their last 5 test attempts.

    Args:
        user_id: The ID of the user.
        category: One of 'aptitude', 'coding', 'core'.

    Returns:
        Integer score 0-100. Returns 0 if no attempts found.
    """
    attempts = (TestAttempt.query
                .filter_by(user_id=user_id, category=category)
                .order_by(TestAttempt.attempted_at.desc())
                .limit(5)
                .all())
    if not attempts:
        return 0
    return round(sum(a.score for a in attempts) / len(attempts))


def format_seconds(seconds: int) -> str:
    """
    Converts integer seconds to mm:ss string.
    Example: 125 → '02:05'
    Used in templates via a Jinja2 filter or directly in routes.
    """
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def get_readiness_label(aptitude: int, coding: int, core: int) -> str:
    """
    Returns placement readiness label based on 3 category scores.

    Args:
        aptitude: Aptitude score 0-100.
        coding:   Coding score 0-100.
        core:     Core score 0-100.

    Returns:
        'High'   if average >= 70
        'Medium' if average >= 40
        'Low'    if average < 40
        'N/A'    if all three scores are 0
    """
    if aptitude == 0 and coding == 0 and core == 0:
        return 'N/A'
    average = (aptitude + coding + core) / 3
    if average >= 70:
        return 'High'
    elif average >= 40:
        return 'Medium'
    return 'Low'

from app.models import Leaderboard, Notification, TestAttempt
from app.extensions import db
from sqlalchemy import func
import json
from datetime import datetime

def compute_badge(tests_taken: int, avg_score: float) -> str:
    """
    Return badge string based on thresholds:
      'Advanced'     — tests_taken >= 15 AND avg_score >= 70
      'Intermediate' — tests_taken >= 5  AND avg_score >= 40
      'Beginner'     — everything else
    """
    if tests_taken >= 15 and avg_score >= 70:
        return 'Advanced'
    if tests_taken >= 5 and avg_score >= 40:
        return 'Intermediate'
    return 'Beginner'

def update_leaderboard(user_id: int) -> None:
    """
    Called after every test submission. Recalculates and upserts
    the Leaderboard row for the given user.
    """
    try:
        attempts = TestAttempt.query.filter_by(user_id=user_id).all()
        
        tests_taken = len(attempts)
        total_score = sum(a.score for a in attempts)
        avg_score   = round(total_score / tests_taken, 2) if tests_taken > 0 else 0
        
        new_badge = compute_badge(tests_taken, avg_score)
        
        lb = Leaderboard.query.filter_by(user_id=user_id).first()
        if lb is None:
            lb = Leaderboard(user_id=user_id)
            db.session.add(lb)
            
        old_badge = lb.badge
        lb.total_score  = total_score
        lb.tests_taken  = tests_taken
        lb.badge        = new_badge
        lb.last_updated = datetime.utcnow()
        db.session.commit()
        
        if new_badge != old_badge:
            push_notification(user_id,
                f"Congratulations! You reached {new_badge} level!",
                type='success')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(str(e))

def push_notification(user_id: int, message: str, type: str = 'info') -> None:
    """
    Insert a new Notification row for the user.
    """
    try:
        n = Notification(
            user_id=user_id,
            message=message,
            type=type,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.session.add(n)
        db.session.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Failed to push notification: " + str(e))
