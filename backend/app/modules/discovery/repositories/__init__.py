"""Discovery repositories package."""

from app.modules.discovery.repositories.activity_selection_repository import (
    DiscoveryActivitySelectionRepository,
)
from app.modules.discovery.repositories.onet_repository import (
    OnetDwaRepository,
    OnetGwaRepository,
    OnetIwaRepository,
    OnetOccupationRepository,
)
from app.modules.discovery.repositories.role_mapping_repository import (
    DiscoveryRoleMappingRepository,
)
from app.modules.discovery.repositories.session_repository import (
    DiscoverySessionRepository,
)
from app.modules.discovery.repositories.upload_repository import (
    DiscoveryUploadRepository,
)

__all__ = [
    "DiscoveryActivitySelectionRepository",
    "DiscoveryRoleMappingRepository",
    "DiscoverySessionRepository",
    "DiscoveryUploadRepository",
    "OnetDwaRepository",
    "OnetGwaRepository",
    "OnetIwaRepository",
    "OnetOccupationRepository",
]
