"""Integration tests for role mapping agent flow.

Tests the complete flow from roles to O*NET mappings using the
LLM-powered RoleMappingAgent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.role_mapping_agent import (
    ConfidenceTier,
    RoleMappingAgent,
    RoleMappingResult,
)
from app.models.onet_occupation import OnetOccupation
from app.repositories.onet_repository import OnetRepository
from app.services.llm_service import LLMService


class TestRoleMappingAgentIntegration:
    """Integration tests for role mapping agent."""

    @pytest.mark.asyncio
    async def test_full_mapping_flow(self):
        """Test complete flow from roles to mappings."""
        # Create mock LLM that returns valid JSON
        mock_llm = AsyncMock(spec=LLMService)
        mock_llm.generate_response.return_value = """[
            {
                "role": "Software Engineer",
                "onet_code": "15-1252.00",
                "onet_title": "Software Developers",
                "confidence": "HIGH",
                "reasoning": "Direct match for software development role"
            },
            {
                "role": "Data Analyst",
                "onet_code": "15-2051.00",
                "onet_title": "Data Scientists",
                "confidence": "MEDIUM",
                "reasoning": "Data analysis is part of data science"
            }
        ]"""

        # Create mock occupation objects
        mock_occupations = [
            MagicMock(
                spec=OnetOccupation,
                code="15-1252.00",
                title="Software Developers",
                description="Develop software applications",
            ),
            MagicMock(
                spec=OnetOccupation,
                code="15-2051.00",
                title="Data Scientists",
                description="Analyze data using statistical methods",
            ),
        ]

        # Create mock repository that returns candidates
        mock_repo = AsyncMock(spec=OnetRepository)
        mock_repo.search_with_full_text.return_value = mock_occupations

        # Create agent and run mapping
        agent = RoleMappingAgent(
            llm_service=mock_llm,
            onet_repository=mock_repo,
        )
        results = await agent.map_roles(["Software Engineer", "Data Analyst"])

        # Verify results
        assert len(results) == 2

        assert results[0].source_role == "Software Engineer"
        assert results[0].onet_code == "15-1252.00"
        assert results[0].confidence == ConfidenceTier.HIGH
        assert results[0].confidence_score == 0.95

        assert results[1].source_role == "Data Analyst"
        assert results[1].onet_code == "15-2051.00"
        assert results[1].confidence == ConfidenceTier.MEDIUM
        assert results[1].confidence_score == 0.75

    @pytest.mark.asyncio
    async def test_handles_llm_failure_gracefully(self):
        """Test that agent handles LLM failures with fallbacks."""
        mock_llm = AsyncMock(spec=LLMService)
        mock_llm.generate_response.side_effect = Exception("LLM API error")

        mock_occupation = MagicMock(
            spec=OnetOccupation,
            code="15-1252.00",
            title="Software Developers",
            description="Develop software",
        )

        mock_repo = AsyncMock(spec=OnetRepository)
        mock_repo.search_with_full_text.return_value = [mock_occupation]

        agent = RoleMappingAgent(
            llm_service=mock_llm,
            onet_repository=mock_repo,
        )
        results = await agent.map_roles(["Software Engineer"])

        # Should return fallback result with LOW confidence
        assert len(results) == 1
        assert results[0].confidence == ConfidenceTier.LOW
        assert "Fallback" in results[0].reasoning
        assert results[0].onet_code == "15-1252.00"  # Uses first candidate

    @pytest.mark.asyncio
    async def test_handles_no_candidates_found(self):
        """Test handling when no O*NET candidates are found."""
        mock_llm = AsyncMock(spec=LLMService)
        mock_llm.generate_response.return_value = """[
            {
                "role": "Obscure Job Title",
                "onet_code": null,
                "onet_title": null,
                "confidence": "LOW",
                "reasoning": "No matching occupation found"
            }
        ]"""

        mock_repo = AsyncMock(spec=OnetRepository)
        mock_repo.search_with_full_text.return_value = []  # No candidates

        agent = RoleMappingAgent(
            llm_service=mock_llm,
            onet_repository=mock_repo,
        )
        results = await agent.map_roles(["Obscure Job Title"])

        assert len(results) == 1
        assert results[0].onet_code is None
        assert results[0].confidence == ConfidenceTier.LOW

    @pytest.mark.asyncio
    async def test_batches_large_role_lists(self):
        """Test that large role lists are batched correctly."""
        import json

        mock_llm = AsyncMock(spec=LLMService)

        # Track batch calls to return correct results for each batch
        batch_call_count = [0]
        batch_sizes = [5, 5, 2]  # Expected: 12 roles in batches of 5

        def generate_batch_response(*args, **kwargs):
            batch_idx = batch_call_count[0]
            batch_call_count[0] += 1
            batch_size = batch_sizes[batch_idx] if batch_idx < len(batch_sizes) else 0

            # Calculate starting role index for this batch
            start_idx = sum(batch_sizes[:batch_idx])
            results = []
            for i in range(batch_size):
                role_idx = start_idx + i
                results.append({
                    "role": f"Role {role_idx}",
                    "onet_code": "15-1252.00",
                    "onet_title": "Software Developers",
                    "confidence": "MEDIUM",
                    "reasoning": "Batch test",
                })
            return json.dumps(results)

        mock_llm.generate_response.side_effect = generate_batch_response

        mock_occupation = MagicMock(
            spec=OnetOccupation,
            code="15-1252.00",
            title="Software Developers",
            description="Develop software",
        )
        mock_repo = AsyncMock(spec=OnetRepository)
        mock_repo.search_with_full_text.return_value = [mock_occupation]

        # Use batch_size of 5 for testing
        agent = RoleMappingAgent(
            llm_service=mock_llm,
            onet_repository=mock_repo,
            batch_size=5,
        )

        # Create 12 roles - should result in 3 batches (5, 5, 2)
        roles = [f"Role {i}" for i in range(12)]
        results = await agent.map_roles(roles)

        # Should have 12 results
        assert len(results) == 12
        # LLM should be called 3 times (3 batches)
        assert mock_llm.generate_response.call_count == 3

    @pytest.mark.asyncio
    async def test_handles_malformed_llm_response(self):
        """Test handling of malformed JSON from LLM."""
        mock_llm = AsyncMock(spec=LLMService)
        mock_llm.generate_response.return_value = "This is not valid JSON"

        mock_occupation = MagicMock(
            spec=OnetOccupation,
            code="15-1252.00",
            title="Software Developers",
            description="Develop software",
        )
        mock_repo = AsyncMock(spec=OnetRepository)
        mock_repo.search_with_full_text.return_value = [mock_occupation]

        agent = RoleMappingAgent(
            llm_service=mock_llm,
            onet_repository=mock_repo,
        )
        results = await agent.map_roles(["Software Engineer"])

        # Should return fallback with parse error
        assert len(results) == 1
        assert results[0].confidence == ConfidenceTier.LOW
        assert "Parse error" in results[0].reasoning

    @pytest.mark.asyncio
    async def test_handles_markdown_code_blocks(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        mock_llm = AsyncMock(spec=LLMService)
        mock_llm.generate_response.return_value = """```json
[
    {
        "role": "Project Manager",
        "onet_code": "11-9199.00",
        "onet_title": "Managers, All Other",
        "confidence": "MEDIUM",
        "reasoning": "General management role"
    }
]
```"""

        mock_occupation = MagicMock(
            spec=OnetOccupation,
            code="11-9199.00",
            title="Managers, All Other",
            description="Management duties",
        )
        mock_repo = AsyncMock(spec=OnetRepository)
        mock_repo.search_with_full_text.return_value = [mock_occupation]

        agent = RoleMappingAgent(
            llm_service=mock_llm,
            onet_repository=mock_repo,
        )
        results = await agent.map_roles(["Project Manager"])

        assert len(results) == 1
        assert results[0].onet_code == "11-9199.00"
        assert results[0].confidence == ConfidenceTier.MEDIUM

    @pytest.mark.asyncio
    async def test_empty_role_list_returns_empty(self):
        """Test that empty role list returns empty results."""
        mock_llm = AsyncMock(spec=LLMService)
        mock_repo = AsyncMock(spec=OnetRepository)

        agent = RoleMappingAgent(
            llm_service=mock_llm,
            onet_repository=mock_repo,
        )
        results = await agent.map_roles([])

        assert results == []
        mock_llm.generate_response.assert_not_called()
        mock_repo.search_with_full_text.assert_not_called()


class TestRoleMappingServiceIntegration:
    """Integration tests for role mapping service with agent."""

    @pytest.mark.asyncio
    async def test_service_uses_agent_when_available(self):
        """Test that service delegates to agent when configured."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = AsyncMock()
        mock_agent = AsyncMock()
        mock_upload_service = AsyncMock()

        # Setup upload service mocks
        mock_upload_service.get_file_content.return_value = b"role\nEngineer\nAnalyst\n"
        mock_upload = MagicMock()
        mock_upload.file_name = "roles.csv"
        mock_upload_service.repository.get_by_id.return_value = mock_upload

        # Setup agent mock
        mock_agent.map_roles.return_value = [
            RoleMappingResult(
                source_role="Engineer",
                onet_code="15-1252.00",
                onet_title="Software Developers",
                confidence=ConfidenceTier.HIGH,
                reasoning="Direct match",
            ),
            RoleMappingResult(
                source_role="Analyst",
                onet_code="15-2051.00",
                onet_title="Data Scientists",
                confidence=ConfidenceTier.MEDIUM,
                reasoning="Related role",
            ),
        ]

        # Setup repository mock for mapping creation
        mock_mapping = MagicMock()
        mock_mapping.id = "test-id"
        mock_mapping.source_role = "Engineer"
        mock_mapping.onet_code = "15-1252.00"
        mock_mapping.confidence_score = 0.95
        mock_mapping.row_count = 1
        mock_mapping.user_confirmed = False
        mock_repo.create.return_value = mock_mapping

        service = RoleMappingService(
            repository=mock_repo,
            upload_service=mock_upload_service,
            role_mapping_agent=mock_agent,
        )

        # Mock file parser
        from unittest.mock import patch
        with patch.object(service, "_file_parser") as mock_parser:
            mock_parser.extract_unique_values.return_value = [
                {"value": "Engineer", "count": 1},
                {"value": "Analyst", "count": 1},
            ]

            import uuid
            results = await service.create_mappings_from_upload(
                session_id=uuid.uuid4(),
                upload_id=uuid.uuid4(),
                role_column="role",
            )

        # Agent should be called
        mock_agent.map_roles.assert_called_once_with(["Engineer", "Analyst"])
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_service_falls_back_to_fuzzy_without_agent(self):
        """Test that service uses fuzzy matcher when no agent configured."""
        from app.services.role_mapping_service import RoleMappingService

        mock_repo = AsyncMock()
        mock_onet_client = AsyncMock()
        mock_fuzzy_matcher = MagicMock()
        mock_upload_service = AsyncMock()

        # Setup upload service mocks
        mock_upload_service.get_file_content.return_value = b"role\nEngineer\n"
        mock_upload = MagicMock()
        mock_upload.file_name = "roles.csv"
        mock_upload_service.repository.get_by_id.return_value = mock_upload

        # Setup O*NET client mock
        mock_onet_client.search_occupations.return_value = [
            {"code": "15-1252.00", "title": "Software Developers"}
        ]

        # Setup fuzzy matcher mock
        mock_fuzzy_matcher.find_best_matches.return_value = [
            {"code": "15-1252.00", "title": "Software Developers", "score": 0.85}
        ]

        # Setup repository mock
        mock_mapping = MagicMock()
        mock_mapping.id = "test-id"
        mock_mapping.source_role = "Engineer"
        mock_mapping.onet_code = "15-1252.00"
        mock_mapping.confidence_score = 0.85
        mock_mapping.row_count = 1
        mock_mapping.user_confirmed = False
        mock_repo.create.return_value = mock_mapping

        service = RoleMappingService(
            repository=mock_repo,
            onet_client=mock_onet_client,
            upload_service=mock_upload_service,
            fuzzy_matcher=mock_fuzzy_matcher,
            role_mapping_agent=None,  # No agent
        )

        from unittest.mock import patch
        with patch.object(service, "_file_parser") as mock_parser:
            mock_parser.extract_unique_values.return_value = [
                {"value": "Engineer", "count": 1},
            ]

            import uuid
            results = await service.create_mappings_from_upload(
                session_id=uuid.uuid4(),
                upload_id=uuid.uuid4(),
                role_column="role",
            )

        # Fuzzy matcher should be called
        mock_fuzzy_matcher.find_best_matches.assert_called_once()
        assert len(results) == 1
