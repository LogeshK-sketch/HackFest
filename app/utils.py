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
