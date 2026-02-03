"""SQLAlchemy models package."""
from app.models.base import Base, async_session_maker, get_async_session
from app.models.onet_occupation import OnetAlternateTitle, OnetOccupation, OnetSyncLog
from app.models.onet_work_activities import OnetGWA, OnetIWA, OnetDWA
from app.models.onet_task import OnetTask, OnetTaskToDWA
from app.models.onet_skills import OnetSkill, OnetTechnologySkill
from app.models.discovery_session import DiscoverySession, SessionStatus
from app.models.discovery_upload import DiscoveryUpload
from app.models.discovery_role_mapping import DiscoveryRoleMapping
from app.models.discovery_activity_selection import DiscoveryActivitySelection
from app.models.discovery_analysis import DiscoveryAnalysisResult, AnalysisDimension
from app.models.agentification_candidate import AgentificationCandidate, PriorityTier

__all__ = [
    # Base
    "Base",
    "async_session_maker",
    "get_async_session",
    # O*NET Reference Models
    "OnetOccupation",
    "OnetAlternateTitle",
    "OnetSyncLog",
    "OnetGWA",
    "OnetIWA",
    "OnetDWA",
    "OnetTask",
    "OnetTaskToDWA",
    "OnetSkill",
    "OnetTechnologySkill",
    # Application Models
    "DiscoverySession",
    "SessionStatus",
    "DiscoveryUpload",
    "DiscoveryRoleMapping",
    "DiscoveryActivitySelection",
    "DiscoveryAnalysisResult",
    "AnalysisDimension",
    "AgentificationCandidate",
    "PriorityTier",
]
