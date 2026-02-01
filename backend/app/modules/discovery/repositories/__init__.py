"""Discovery repositories package."""

from app.modules.discovery.repositories.activity_selection_repository import (
    DiscoveryActivitySelectionRepository,
)
from app.modules.discovery.repositories.analysis_result_repository import (
    DiscoveryAnalysisResultRepository,
)
from app.modules.discovery.repositories.candidate_repository import (
    AgentificationCandidateRepository,
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
    "AgentificationCandidateRepository",
    "DiscoveryActivitySelectionRepository",
    "DiscoveryAnalysisResultRepository",
    "DiscoveryRoleMappingRepository",
    "DiscoverySessionRepository",
    "DiscoveryUploadRepository",
    "OnetDwaRepository",
    "OnetGwaRepository",
    "OnetIwaRepository",
    "OnetOccupationRepository",
]
