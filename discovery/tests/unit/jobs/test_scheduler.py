# discovery/tests/unit/jobs/test_scheduler.py
"""Unit tests for job scheduler."""
import pytest


def test_scheduler_exists():
    """Test Scheduler is importable."""
    from app.jobs.scheduler import JobScheduler
    assert JobScheduler is not None


def test_scheduler_can_add_job():
    """Test adding a job to scheduler."""
    from app.jobs.scheduler import JobScheduler

    scheduler = JobScheduler()
    assert hasattr(scheduler, "add_job")


def test_scheduler_can_start():
    """Test scheduler can start."""
    from app.jobs.scheduler import JobScheduler

    scheduler = JobScheduler()
    assert hasattr(scheduler, "start")
    assert hasattr(scheduler, "shutdown")


def test_scheduler_get_jobs():
    """Test getting list of jobs."""
    from app.jobs.scheduler import JobScheduler

    scheduler = JobScheduler()
    jobs = scheduler.get_jobs()
    assert isinstance(jobs, list)
