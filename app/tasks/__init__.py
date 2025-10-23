"""
Background tasks for Coffee Shop API.

Tasks:
- cleanup: Automated deletion of unverified users
"""

from app.tasks import cleanup

__all__ = ['cleanup']
