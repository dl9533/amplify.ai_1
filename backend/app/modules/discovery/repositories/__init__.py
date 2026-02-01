"""Discovery repositories package."""

from app.modules.discovery.repositories.onet_repository import (
    OnetDwaRepository,
    OnetGwaRepository,
    OnetIwaRepository,
    OnetOccupationRepository,
)

__all__ = [
    "OnetDwaRepository",
    "OnetGwaRepository",
    "OnetIwaRepository",
    "OnetOccupationRepository",
]
