"""Tests for verifying module exports from the main discovery app module.

This test file ensures all public APIs (services, agents, routers, schemas)
are properly exported from the top-level app module.
"""
import pytest


class TestServicesExported:
    """Test that all services are exported from the app module."""

    def test_activity_service_exported(self):
        """ActivityService should be importable from app module."""
        from app import ActivityService
        assert ActivityService is not None

    def test_analysis_service_exported(self):
        """AnalysisService should be importable from app module."""
        from app import AnalysisService
        assert AnalysisService is not None

    def test_chat_service_exported(self):
        """ChatService should be importable from app module."""
        from app import ChatService
        assert ChatService is not None

    def test_context_service_exported(self):
        """ContextService should be importable from app module."""
        from app import ContextService
        assert ContextService is not None

    def test_export_service_exported(self):
        """ExportService should be importable from app module."""
        from app import ExportService
        assert ExportService is not None

    def test_handoff_service_exported(self):
        """HandoffService should be importable from app module."""
        from app import HandoffService
        assert HandoffService is not None

    def test_agent_memory_service_exported(self):
        """AgentMemoryService should be importable from app module."""
        from app import AgentMemoryService
        assert AgentMemoryService is not None

    def test_roadmap_service_exported(self):
        """RoadmapService should be importable from app module."""
        from app import RoadmapService
        assert RoadmapService is not None

    def test_role_mapping_service_exported(self):
        """RoleMappingService should be importable from app module."""
        from app import RoleMappingService
        assert RoleMappingService is not None

    def test_onet_service_exported(self):
        """OnetService should be importable from app module."""
        from app import OnetService
        assert OnetService is not None

    def test_scoring_service_exported(self):
        """ScoringService should be importable from app module."""
        from app import ScoringService
        assert ScoringService is not None

    def test_session_service_exported(self):
        """SessionService should be importable from app module."""
        from app import SessionService
        assert SessionService is not None

    def test_upload_service_exported(self):
        """UploadService should be importable from app module."""
        from app import UploadService
        assert UploadService is not None


class TestServiceDependencyFunctionsExported:
    """Test that dependency injection functions are exported."""

    def test_get_activity_service_exported(self):
        """get_activity_service should be importable from app module."""
        from app import get_activity_service
        assert callable(get_activity_service)

    def test_get_analysis_service_exported(self):
        """get_analysis_service should be importable from app module."""
        from app import get_analysis_service
        assert callable(get_analysis_service)

    def test_get_chat_service_exported(self):
        """get_chat_service should be importable from app module."""
        from app import get_chat_service
        assert callable(get_chat_service)

    def test_get_context_service_exported(self):
        """get_context_service should be importable from app module."""
        from app import get_context_service
        assert callable(get_context_service)

    def test_get_export_service_exported(self):
        """get_export_service should be importable from app module."""
        from app import get_export_service
        assert callable(get_export_service)

    def test_get_handoff_service_exported(self):
        """get_handoff_service should be importable from app module."""
        from app import get_handoff_service
        assert callable(get_handoff_service)

    def test_get_roadmap_service_exported(self):
        """get_roadmap_service should be importable from app module."""
        from app import get_roadmap_service
        assert callable(get_roadmap_service)

    def test_get_role_mapping_service_exported(self):
        """get_role_mapping_service should be importable from app module."""
        from app import get_role_mapping_service
        assert callable(get_role_mapping_service)

    def test_get_onet_service_exported(self):
        """get_onet_service should be importable from app module."""
        from app import get_onet_service
        assert callable(get_onet_service)

    def test_get_scoring_service_exported(self):
        """get_scoring_service should be importable from app module."""
        from app import get_scoring_service
        assert callable(get_scoring_service)

    def test_get_session_service_exported(self):
        """get_session_service should be importable from app module."""
        from app import get_session_service
        assert callable(get_session_service)

    def test_get_upload_service_exported(self):
        """get_upload_service should be importable from app module."""
        from app import get_upload_service
        assert callable(get_upload_service)


class TestAgentsExported:
    """Test that all agents are exported from the app module."""

    def test_discovery_orchestrator_exported(self):
        """DiscoveryOrchestrator should be importable from app module."""
        from app import DiscoveryOrchestrator
        assert DiscoveryOrchestrator is not None

    def test_base_subagent_exported(self):
        """BaseSubagent should be importable from app module."""
        from app import BaseSubagent
        assert BaseSubagent is not None

    def test_upload_subagent_exported(self):
        """UploadSubagent should be importable from app module."""
        from app import UploadSubagent
        assert UploadSubagent is not None

    def test_mapping_subagent_exported(self):
        """MappingSubagent should be importable from app module."""
        from app import MappingSubagent
        assert MappingSubagent is not None

    def test_activity_subagent_exported(self):
        """ActivitySubagent should be importable from app module."""
        from app import ActivitySubagent
        assert ActivitySubagent is not None

    def test_analysis_subagent_exported(self):
        """AnalysisSubagent should be importable from app module."""
        from app import AnalysisSubagent
        assert AnalysisSubagent is not None

    def test_roadmap_subagent_exported(self):
        """RoadmapSubagent should be importable from app module."""
        from app import RoadmapSubagent
        assert RoadmapSubagent is not None

    def test_quick_action_chip_generator_exported(self):
        """QuickActionChipGenerator should be importable from app module."""
        from app import QuickActionChipGenerator
        assert QuickActionChipGenerator is not None

    def test_chat_message_formatter_exported(self):
        """ChatMessageFormatter should be importable from app module."""
        from app import ChatMessageFormatter
        assert ChatMessageFormatter is not None

    def test_brainstorming_handler_exported(self):
        """BrainstormingHandler should be importable from app module."""
        from app import BrainstormingHandler
        assert BrainstormingHandler is not None


class TestAgentSupportTypesExported:
    """Test that agent support types are exported."""

    def test_chip_type_exported(self):
        """Chip type should be importable from app module."""
        from app import Chip
        assert Chip is not None

    def test_conversation_turn_exported(self):
        """ConversationTurn type should be importable from app module."""
        from app import ConversationTurn
        assert ConversationTurn is not None

    def test_formatted_message_exported(self):
        """FormattedMessage type should be importable from app module."""
        from app import FormattedMessage
        assert FormattedMessage is not None

    def test_formatted_question_exported(self):
        """FormattedQuestion type should be importable from app module."""
        from app import FormattedQuestion
        assert FormattedQuestion is not None

    def test_parsed_response_exported(self):
        """ParsedResponse type should be importable from app module."""
        from app import ParsedResponse
        assert ParsedResponse is not None

    def test_quick_action_exported(self):
        """QuickAction type should be importable from app module."""
        from app import QuickAction
        assert QuickAction is not None


class TestRoutersExported:
    """Test that all routers are exported from the app module."""

    def test_activities_router_exported(self):
        """activities_router should be importable from app module."""
        from app import activities_router
        assert activities_router is not None

    def test_analysis_router_exported(self):
        """analysis_router should be importable from app module."""
        from app import analysis_router
        assert analysis_router is not None

    def test_chat_router_exported(self):
        """chat_router should be importable from app module."""
        from app import chat_router
        assert chat_router is not None

    def test_exports_router_exported(self):
        """exports_router should be importable from app module."""
        from app import exports_router
        assert exports_router is not None

    def test_handoff_router_exported(self):
        """handoff_router should be importable from app module."""
        from app import handoff_router
        assert handoff_router is not None

    def test_roadmap_router_exported(self):
        """roadmap_router should be importable from app module."""
        from app import roadmap_router
        assert roadmap_router is not None

    def test_role_mappings_router_exported(self):
        """role_mappings_router should be importable from app module."""
        from app import role_mappings_router
        assert role_mappings_router is not None

    def test_sessions_router_exported(self):
        """sessions_router should be importable from app module."""
        from app import sessions_router
        assert sessions_router is not None

    def test_uploads_router_exported(self):
        """uploads_router should be importable from app module."""
        from app import uploads_router
        assert uploads_router is not None


class TestSchemasExported:
    """Test that all schemas are exported from the app module."""

    # Activity schemas
    def test_activity_selection_update_exported(self):
        """ActivitySelectionUpdate should be importable from app module."""
        from app import ActivitySelectionUpdate
        assert ActivitySelectionUpdate is not None

    def test_bulk_selection_request_exported(self):
        """BulkSelectionRequest should be importable from app module."""
        from app import BulkSelectionRequest
        assert BulkSelectionRequest is not None

    def test_bulk_selection_response_exported(self):
        """BulkSelectionResponse should be importable from app module."""
        from app import BulkSelectionResponse
        assert BulkSelectionResponse is not None

    def test_dwa_response_exported(self):
        """DWAResponse should be importable from app module."""
        from app import DWAResponse
        assert DWAResponse is not None

    def test_gwa_group_response_exported(self):
        """GWAGroupResponse should be importable from app module."""
        from app import GWAGroupResponse
        assert GWAGroupResponse is not None

    def test_selection_count_response_exported(self):
        """SelectionCountResponse should be importable from app module."""
        from app import SelectionCountResponse
        assert SelectionCountResponse is not None

    # Analysis schemas
    def test_all_dimensions_response_exported(self):
        """AllDimensionsResponse should be importable from app module."""
        from app import AllDimensionsResponse
        assert AllDimensionsResponse is not None

    def test_analysis_dimension_exported(self):
        """AnalysisDimension should be importable from app module."""
        from app import AnalysisDimension
        assert AnalysisDimension is not None

    def test_analysis_result_exported(self):
        """AnalysisResult should be importable from app module."""
        from app import AnalysisResult
        assert AnalysisResult is not None

    def test_dimension_analysis_response_exported(self):
        """DimensionAnalysisResponse should be importable from app module."""
        from app import DimensionAnalysisResponse
        assert DimensionAnalysisResponse is not None

    def test_dimension_summary_exported(self):
        """DimensionSummary should be importable from app module."""
        from app import DimensionSummary
        assert DimensionSummary is not None

    def test_priority_tier_exported(self):
        """PriorityTier should be importable from app module."""
        from app import PriorityTier
        assert PriorityTier is not None

    def test_trigger_analysis_response_exported(self):
        """TriggerAnalysisResponse should be importable from app module."""
        from app import TriggerAnalysisResponse
        assert TriggerAnalysisResponse is not None

    # Chat schemas
    def test_chat_history_item_exported(self):
        """ChatHistoryItem should be importable from app module."""
        from app import ChatHistoryItem
        assert ChatHistoryItem is not None

    def test_chat_message_exported(self):
        """ChatMessage should be importable from app module."""
        from app import ChatMessage
        assert ChatMessage is not None

    def test_chat_response_exported(self):
        """ChatResponse should be importable from app module."""
        from app import ChatResponse
        assert ChatResponse is not None

    def test_quick_action_request_exported(self):
        """QuickActionRequest should be importable from app module."""
        from app import QuickActionRequest
        assert QuickActionRequest is not None

    def test_quick_action_response_exported(self):
        """QuickActionResponse should be importable from app module."""
        from app import QuickActionResponse
        assert QuickActionResponse is not None

    # Export schemas
    def test_handoff_bundle_exported(self):
        """HandoffBundle should be importable from app module."""
        from app import HandoffBundle
        assert HandoffBundle is not None

    # Handoff schemas
    def test_handoff_error_exported(self):
        """HandoffError should be importable from app module."""
        from app import HandoffError
        assert HandoffError is not None

    def test_handoff_request_exported(self):
        """HandoffRequest should be importable from app module."""
        from app import HandoffRequest
        assert HandoffRequest is not None

    def test_handoff_response_exported(self):
        """HandoffResponse should be importable from app module."""
        from app import HandoffResponse
        assert HandoffResponse is not None

    def test_handoff_status_exported(self):
        """HandoffStatus should be importable from app module."""
        from app import HandoffStatus
        assert HandoffStatus is not None

    def test_validation_result_exported(self):
        """ValidationResult should be importable from app module."""
        from app import ValidationResult
        assert ValidationResult is not None

    # Roadmap schemas
    def test_bulk_phase_update_exported(self):
        """BulkPhaseUpdate should be importable from app module."""
        from app import BulkPhaseUpdate
        assert BulkPhaseUpdate is not None

    def test_bulk_update_request_exported(self):
        """BulkUpdateRequest should be importable from app module."""
        from app import BulkUpdateRequest
        assert BulkUpdateRequest is not None

    def test_bulk_update_response_exported(self):
        """BulkUpdateResponse should be importable from app module."""
        from app import BulkUpdateResponse
        assert BulkUpdateResponse is not None

    def test_estimated_effort_exported(self):
        """EstimatedEffort should be importable from app module."""
        from app import EstimatedEffort
        assert EstimatedEffort is not None

    def test_phase_update_exported(self):
        """PhaseUpdate should be importable from app module."""
        from app import PhaseUpdate
        assert PhaseUpdate is not None

    def test_reorder_request_exported(self):
        """ReorderRequest should be importable from app module."""
        from app import ReorderRequest
        assert ReorderRequest is not None

    def test_reorder_response_exported(self):
        """ReorderResponse should be importable from app module."""
        from app import ReorderResponse
        assert ReorderResponse is not None

    def test_roadmap_item_exported(self):
        """RoadmapItem should be importable from app module."""
        from app import RoadmapItem
        assert RoadmapItem is not None

    def test_roadmap_items_response_exported(self):
        """RoadmapItemsResponse should be importable from app module."""
        from app import RoadmapItemsResponse
        assert RoadmapItemsResponse is not None

    def test_roadmap_phase_exported(self):
        """RoadmapPhase should be importable from app module."""
        from app import RoadmapPhase
        assert RoadmapPhase is not None

    # Role mapping schemas
    def test_bulk_confirm_request_exported(self):
        """BulkConfirmRequest should be importable from app module."""
        from app import BulkConfirmRequest
        assert BulkConfirmRequest is not None

    def test_bulk_confirm_response_exported(self):
        """BulkConfirmResponse should be importable from app module."""
        from app import BulkConfirmResponse
        assert BulkConfirmResponse is not None

    def test_onet_occupation_exported(self):
        """OnetOccupation should be importable from app module."""
        from app import OnetOccupation
        assert OnetOccupation is not None

    def test_onet_search_result_exported(self):
        """OnetSearchResult should be importable from app module."""
        from app import OnetSearchResult
        assert OnetSearchResult is not None

    def test_role_mapping_response_exported(self):
        """RoleMappingResponse should be importable from app module."""
        from app import RoleMappingResponse
        assert RoleMappingResponse is not None

    def test_role_mapping_update_exported(self):
        """RoleMappingUpdate should be importable from app module."""
        from app import RoleMappingUpdate
        assert RoleMappingUpdate is not None

    # Session schemas
    def test_session_create_exported(self):
        """SessionCreate should be importable from app module."""
        from app import SessionCreate
        assert SessionCreate is not None

    def test_session_response_exported(self):
        """SessionResponse should be importable from app module."""
        from app import SessionResponse
        assert SessionResponse is not None

    def test_session_list_exported(self):
        """SessionList should be importable from app module."""
        from app import SessionList
        assert SessionList is not None

    def test_step_update_exported(self):
        """StepUpdate should be importable from app module."""
        from app import StepUpdate
        assert StepUpdate is not None

    # Upload schemas
    def test_column_mapping_update_exported(self):
        """ColumnMappingUpdate should be importable from app module."""
        from app import ColumnMappingUpdate
        assert ColumnMappingUpdate is not None

    def test_upload_response_exported(self):
        """UploadResponse should be importable from app module."""
        from app import UploadResponse
        assert UploadResponse is not None


class TestAllExportsList:
    """Test that __all__ is properly defined."""

    def test_all_list_defined(self):
        """__all__ should be defined in the app module."""
        import app
        assert hasattr(app, '__all__')
        assert isinstance(app.__all__, list)

    def test_all_list_contains_services(self):
        """__all__ should contain all service classes."""
        import app
        services = [
            "ActivityService", "AnalysisService", "ChatService",
            "ContextService", "ExportService", "HandoffService",
            "AgentMemoryService", "RoadmapService", "RoleMappingService",
            "OnetService", "ScoringService", "SessionService", "UploadService",
        ]
        for service in services:
            assert service in app.__all__, f"{service} not in __all__"

    def test_all_list_contains_agents(self):
        """__all__ should contain all agent classes."""
        import app
        agents = [
            "DiscoveryOrchestrator", "BaseSubagent", "UploadSubagent",
            "MappingSubagent", "ActivitySubagent", "AnalysisSubagent",
            "RoadmapSubagent", "QuickActionChipGenerator",
            "ChatMessageFormatter", "BrainstormingHandler",
        ]
        for agent in agents:
            assert agent in app.__all__, f"{agent} not in __all__"

    def test_all_list_contains_routers(self):
        """__all__ should contain all router names."""
        import app
        routers = [
            "activities_router", "analysis_router", "chat_router",
            "exports_router", "handoff_router", "roadmap_router",
            "role_mappings_router", "sessions_router", "uploads_router",
        ]
        for router in routers:
            assert router in app.__all__, f"{router} not in __all__"


class TestBulkImports:
    """Test that bulk imports work correctly."""

    def test_import_all_services_at_once(self):
        """Should be able to import all services in one statement."""
        from app import (
            ActivityService,
            AnalysisService,
            ChatService,
            ContextService,
            ExportService,
            HandoffService,
            AgentMemoryService,
            RoadmapService,
            RoleMappingService,
            OnetService,
            ScoringService,
            SessionService,
            UploadService,
        )
        # All imports should succeed
        assert all([
            ActivityService, AnalysisService, ChatService, ContextService,
            ExportService, HandoffService, AgentMemoryService, RoadmapService,
            RoleMappingService, OnetService, ScoringService, SessionService,
            UploadService,
        ])

    def test_import_all_agents_at_once(self):
        """Should be able to import all agents in one statement."""
        from app import (
            DiscoveryOrchestrator,
            BaseSubagent,
            UploadSubagent,
            MappingSubagent,
            ActivitySubagent,
            AnalysisSubagent,
            RoadmapSubagent,
            QuickActionChipGenerator,
            ChatMessageFormatter,
            BrainstormingHandler,
        )
        # All imports should succeed
        assert all([
            DiscoveryOrchestrator, BaseSubagent, UploadSubagent,
            MappingSubagent, ActivitySubagent, AnalysisSubagent,
            RoadmapSubagent, QuickActionChipGenerator,
            ChatMessageFormatter, BrainstormingHandler,
        ])

    def test_import_all_routers_at_once(self):
        """Should be able to import all routers in one statement."""
        from app import (
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
        # All imports should succeed
        assert all([
            activities_router, analysis_router, chat_router, exports_router,
            handoff_router, roadmap_router, role_mappings_router,
            sessions_router, uploads_router,
        ])
