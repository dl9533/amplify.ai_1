"""Discovery module models package."""

from app.modules.discovery.models.onet import (
    OnetOccupation,
    OnetGwa,
    OnetIwa,
    OnetDwa,
    OnetTask,
    OnetSkill,
    OnetTechnologySkill,
)
from app.modules.discovery.models.session import (
    DiscoverySession,
    DiscoveryUpload,
    DiscoveryRoleMapping,
    DiscoveryActivitySelection,
    DiscoveryAnalysisResult,
    AgentificationCandidate,
)
from app.modules.discovery.models.memory import (
    AgentMemoryWorking,
    AgentMemoryEpisodic,
    AgentMemorySemantic,
)

__all__ = [
    # O*NET models
    "OnetOccupation",
    "OnetGwa",
    "OnetIwa",
    "OnetDwa",
    "OnetTask",
    "OnetSkill",
    "OnetTechnologySkill",
    # Session models
    "DiscoverySession",
    "DiscoveryUpload",
    "DiscoveryRoleMapping",
    "DiscoveryActivitySelection",
    "DiscoveryAnalysisResult",
    "AgentificationCandidate",
    # Memory models
    "AgentMemoryWorking",
    "AgentMemoryEpisodic",
    "AgentMemorySemantic",
]
