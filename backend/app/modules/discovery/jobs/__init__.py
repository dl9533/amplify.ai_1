"""O*NET sync jobs package.

This package provides job scheduling and execution for O*NET data synchronization.
"""

from app.modules.discovery.jobs.scheduler import OnetSyncScheduler

__all__ = [
    "OnetSyncScheduler",
]
