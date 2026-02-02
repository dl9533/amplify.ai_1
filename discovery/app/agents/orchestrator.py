# discovery/app/agents/orchestrator.py
"""Discovery Orchestrator for routing messages to appropriate subagents."""
from typing import Any
from uuid import uuid4

from app.enums import DiscoveryStep
from app.agents.upload_agent import UploadSubagent
from app.agents.mapping_agent import MappingSubagent
from app.agents.activity_agent import ActivitySubagent
from app.agents.analysis_agent import AnalysisSubagent
from app.agents.roadmap_agent import RoadmapSubagent


class DiscoveryOrchestrator:
    """Orchestrates the discovery wizard by routing to subagents."""

    _STEP_ORDER: list[DiscoveryStep] = [
        DiscoveryStep.UPLOAD,
        DiscoveryStep.MAP_ROLES,
        DiscoveryStep.SELECT_ACTIVITIES,
        DiscoveryStep.ANALYZE,
        DiscoveryStep.ROADMAP,
    ]

    def __init__(
        self,
        session: Any,
        services: dict[str, Any],
        memory_service: Any = None,
    ) -> None:
        self._session = session
        self._services = services
        self._memory_service = memory_service
        self._conversation_id: str = str(uuid4())
        self._message_history: list[dict[str, Any]] = []
        self._subagents: dict[str, Any] = {}

        # Initialize subagents with their services
        self._init_subagents()

    def _init_subagents(self) -> None:
        """Initialize subagent instances."""
        if "upload" in self._services:
            self._subagents["upload"] = UploadSubagent(
                session=self._session,
                upload_service=self._services["upload"],
                memory_service=self._memory_service,
            )
        if "mapping" in self._services:
            self._subagents["mapping"] = MappingSubagent(
                session=self._session,
                mapping_service=self._services["mapping"],
                memory_service=self._memory_service,
            )
        if "activity" in self._services:
            self._subagents["activity"] = ActivitySubagent(
                session=self._session,
                activity_service=self._services["activity"],
                memory_service=self._memory_service,
            )
        if "analysis" in self._services:
            self._subagents["analysis"] = AnalysisSubagent(
                session=self._session,
                analysis_service=self._services["analysis"],
                memory_service=self._memory_service,
            )
        if "roadmap" in self._services:
            self._subagents["roadmap"] = RoadmapSubagent(
                session=self._session,
                roadmap_service=self._services["roadmap"],
                memory_service=self._memory_service,
            )

    async def process(self, message: str) -> dict[str, Any]:
        """Process message by routing to appropriate subagent."""
        self._message_history.append({"role": "user", "content": message})

        # Get subagent for current step
        step_to_agent = {
            DiscoveryStep.UPLOAD: "upload",
            DiscoveryStep.MAP_ROLES: "mapping",
            DiscoveryStep.SELECT_ACTIVITIES: "activity",
            DiscoveryStep.ANALYZE: "analysis",
            DiscoveryStep.ROADMAP: "roadmap",
        }

        agent_key = step_to_agent.get(self._session.current_step)
        if not agent_key or agent_key not in self._subagents:
            return {
                "message": "Invalid step or agent not configured.",
                "step_complete": False,
            }

        subagent = self._subagents[agent_key]
        response = await subagent.process(message)

        self._message_history.append({
            "role": "assistant",
            "content": response.get("message", ""),
        })

        # Advance step if complete
        if response.get("step_complete"):
            self._advance_step()

        return response

    def _advance_step(self) -> None:
        """Advance to next step in wizard."""
        current = self._session.current_step
        try:
            idx = self._STEP_ORDER.index(current)
            if idx < len(self._STEP_ORDER) - 1:
                self._session.current_step = self._STEP_ORDER[idx + 1]
        except ValueError:
            pass

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """Get full conversation history."""
        return self._message_history.copy()
