"""Discovery module - public API exports.

This module provides clean exports for all services, agents, routers, and schemas
that make up the Discovery module's public API.

Usage examples:
    # Import services
    from app import ActivityService, ChatService, SessionService

    # Import agents
    from app import DiscoveryOrchestrator, UploadSubagent

    # Import routers for FastAPI
    from app import activities_router, sessions_router

    # Import schemas for request/response models
    from app import SessionCreate, ChatMessage, RoadmapItem
"""

# Services
from app.services import (
    ActivityService,
    AgentMemoryService,
    AnalysisService,
    ChatService,
    ContextService,
    ExportService,
    HandoffService,
    OnetService,
    RoadmapService,
    RoleMappingService,
    ScoringService,
    SessionService,
    UploadService,
    # Dependency injection functions
    get_activity_service,
    get_analysis_service,
    get_chat_service,
    get_context_service,
    get_export_service,
    get_handoff_service,
    get_onet_service,
    get_roadmap_service,
    get_role_mapping_service,
    get_scoring_service,
    get_session_service,
    get_upload_service,
)

# Agents
from app.agents import (
    ActivitySubagent,
    AnalysisSubagent,
    BaseSubagent,
    BrainstormingHandler,
    ChatMessageFormatter,
    Chip,
    ConversationTurn,
    DiscoveryOrchestrator,
    FormattedMessage,
    FormattedQuestion,
    MappingSubagent,
    ParsedResponse,
    QuickAction,
    QuickActionChipGenerator,
    RoadmapSubagent,
    UploadSubagent,
)

# Routers
from app.routers import (
    activities_router,
    analysis_router,
    chat_router,
    exports_router,
    handoff_router,
    roadmap_router,
    role_mappings_router,
    sessions_router,
    uploads_router,
)

# Schemas
from app.schemas import (
    # Activity schemas
    ActivitySelectionUpdate,
    BulkSelectionRequest,
    BulkSelectionResponse,
    DWAResponse,
    GWAGroupResponse,
    SelectionCountResponse,
    # Analysis schemas
    AllDimensionsResponse,
    AnalysisDimension,
    AnalysisResult,
    DimensionAnalysisResponse,
    DimensionSummary,
    PriorityTier,
    TriggerAnalysisResponse,
    # Chat schemas
    ChatHistoryItem,
    ChatMessage,
    ChatResponse,
    QuickActionRequest,
    QuickActionResponse,
    # Export schemas
    HandoffBundle,
    # Handoff schemas
    HandoffError,
    HandoffRequest,
    HandoffResponse,
    HandoffStatus,
    ValidationResult,
    # Roadmap schemas
    BulkPhaseUpdate,
    BulkUpdateRequest,
    BulkUpdateResponse,
    EstimatedEffort,
    PhaseUpdate,
    ReorderRequest,
    ReorderResponse,
    RoadmapItem,
    RoadmapItemsResponse,
    RoadmapPhase,
    # Role mapping schemas
    BulkConfirmRequest,
    BulkConfirmResponse,
    OnetOccupation,
    OnetSearchResult,
    RoleMappingResponse,
    RoleMappingUpdate,
    # Session schemas
    SessionCreate,
    SessionList,
    SessionResponse,
    StepUpdate,
    # Upload schemas
    ColumnMappingUpdate,
    UploadResponse,
)

# Exceptions
from app.exceptions import (
    AnalysisException,
    DiscoveryException,
    FileParseException,
    HandoffException,
    LLMAuthError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    OnetApiError,
    OnetAuthError,
    OnetNotFoundError,
    OnetRateLimitError,
    SessionNotFoundException,
    ValidationException,
)

# Middleware
from app.middleware import (
    AutoSaveMiddleware,
    add_exception_handlers,
)

__all__ = [
    # Services
    "ActivityService",
    "AgentMemoryService",
    "AnalysisService",
    "ChatService",
    "ContextService",
    "ExportService",
    "HandoffService",
    "OnetService",
    "RoadmapService",
    "RoleMappingService",
    "ScoringService",
    "SessionService",
    "UploadService",
    # Service dependency functions
    "get_activity_service",
    "get_analysis_service",
    "get_chat_service",
    "get_context_service",
    "get_export_service",
    "get_handoff_service",
    "get_onet_service",
    "get_roadmap_service",
    "get_role_mapping_service",
    "get_scoring_service",
    "get_session_service",
    "get_upload_service",
    # Agents
    "ActivitySubagent",
    "AnalysisSubagent",
    "BaseSubagent",
    "BrainstormingHandler",
    "ChatMessageFormatter",
    "Chip",
    "ConversationTurn",
    "DiscoveryOrchestrator",
    "FormattedMessage",
    "FormattedQuestion",
    "MappingSubagent",
    "ParsedResponse",
    "QuickAction",
    "QuickActionChipGenerator",
    "RoadmapSubagent",
    "UploadSubagent",
    # Routers
    "activities_router",
    "analysis_router",
    "chat_router",
    "exports_router",
    "handoff_router",
    "roadmap_router",
    "role_mappings_router",
    "sessions_router",
    "uploads_router",
    # Activity schemas
    "ActivitySelectionUpdate",
    "BulkSelectionRequest",
    "BulkSelectionResponse",
    "DWAResponse",
    "GWAGroupResponse",
    "SelectionCountResponse",
    # Analysis schemas
    "AllDimensionsResponse",
    "AnalysisDimension",
    "AnalysisResult",
    "DimensionAnalysisResponse",
    "DimensionSummary",
    "PriorityTier",
    "TriggerAnalysisResponse",
    # Chat schemas
    "ChatHistoryItem",
    "ChatMessage",
    "ChatResponse",
    "QuickActionRequest",
    "QuickActionResponse",
    # Export schemas
    "HandoffBundle",
    # Handoff schemas
    "HandoffError",
    "HandoffRequest",
    "HandoffResponse",
    "HandoffStatus",
    "ValidationResult",
    # Roadmap schemas
    "BulkPhaseUpdate",
    "BulkUpdateRequest",
    "BulkUpdateResponse",
    "EstimatedEffort",
    "PhaseUpdate",
    "ReorderRequest",
    "ReorderResponse",
    "RoadmapItem",
    "RoadmapItemsResponse",
    "RoadmapPhase",
    # Role mapping schemas
    "BulkConfirmRequest",
    "BulkConfirmResponse",
    "OnetOccupation",
    "OnetSearchResult",
    "RoleMappingResponse",
    "RoleMappingUpdate",
    # Session schemas
    "SessionCreate",
    "SessionList",
    "SessionResponse",
    "StepUpdate",
    # Upload schemas
    "ColumnMappingUpdate",
    "UploadResponse",
    # Exceptions
    "AnalysisException",
    "DiscoveryException",
    "FileParseException",
    "HandoffException",
    "LLMAuthError",
    "LLMConnectionError",
    "LLMError",
    "LLMRateLimitError",
    "OnetApiError",
    "OnetAuthError",
    "OnetNotFoundError",
    "OnetRateLimitError",
    "SessionNotFoundException",
    "ValidationException",
    # Middleware
    "AutoSaveMiddleware",
    "add_exception_handlers",
]
