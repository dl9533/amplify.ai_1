"""LLM-powered agent for semantic role-to-O*NET mapping.

This agent replaces fuzzy string matching with Claude-based semantic
understanding for mapping job titles to O*NET occupations.
"""
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.models.onet_occupation import OnetOccupation
from app.repositories.onet_repository import OnetRepository
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ConfidenceTier(Enum):
    """Confidence tiers for role mappings.

    Represents semantic confidence rather than numerical precision.
    """

    HIGH = "HIGH"      # Clear, unambiguous match
    MEDIUM = "MEDIUM"  # Reasonable match with some ambiguity
    LOW = "LOW"        # Best guess, significant uncertainty

    def to_score(self) -> float:
        """Convert tier to numerical score for backwards compatibility.

        Returns:
            Score between 0 and 1.
        """
        return {
            ConfidenceTier.HIGH: 0.95,
            ConfidenceTier.MEDIUM: 0.75,
            ConfidenceTier.LOW: 0.50,
        }[self]


@dataclass
class RoleMappingResult:
    """Result of mapping a role to O*NET occupation.

    Attributes:
        source_role: The original role title being mapped.
        onet_code: Matched O*NET occupation code (e.g., "15-1252.00").
        onet_title: Matched O*NET occupation title.
        confidence: Confidence tier (HIGH, MEDIUM, LOW).
        reasoning: Brief explanation of the match.
    """

    source_role: str
    onet_code: str | None
    onet_title: str | None
    confidence: ConfidenceTier
    reasoning: str

    @property
    def confidence_score(self) -> float:
        """Get numerical confidence score for backwards compatibility.

        Returns:
            Score between 0 and 1.
        """
        return self.confidence.to_score()


SYSTEM_PROMPT = """You are an expert at mapping job titles to O*NET occupations.

For each role provided, select the best matching O*NET occupation from the candidates listed.

Return your confidence level:
- HIGH: Clear, unambiguous match (the role title clearly describes this occupation)
- MEDIUM: Reasonable match but some ambiguity (could be this or a related occupation)
- LOW: Best guess, significant uncertainty (role title is vague or doesn't match well)

Respond with a JSON array containing objects with these fields:
- role: The original role title (exactly as provided)
- onet_code: The selected O*NET code (e.g., "15-1252.00")
- onet_title: The selected O*NET title
- confidence: HIGH, MEDIUM, or LOW
- reasoning: Brief explanation (1 sentence)

If no candidates are a good match, use onet_code: null and confidence: LOW."""


class RoleMappingAgent:
    """LLM-powered agent for semantic role-to-O*NET mapping.

    Replaces fuzzy string matching with Claude-based semantic understanding.
    Processes roles in batches for efficiency.

    Attributes:
        llm_service: LLM service for Claude API calls.
        onet_repository: Repository for O*NET data.
        batch_size: Number of roles per LLM call.
        candidates_per_role: Number of O*NET candidates to retrieve per role.
    """

    DEFAULT_BATCH_SIZE = 12
    DEFAULT_CANDIDATES_PER_ROLE = 20

    def __init__(
        self,
        llm_service: LLMService,
        onet_repository: OnetRepository,
        batch_size: int = DEFAULT_BATCH_SIZE,
        candidates_per_role: int = DEFAULT_CANDIDATES_PER_ROLE,
    ) -> None:
        """Initialize the role mapping agent.

        Args:
            llm_service: LLM service for Claude API calls.
            onet_repository: Repository for O*NET data.
            batch_size: Number of roles per LLM call.
            candidates_per_role: Number of O*NET candidates to retrieve per role.
        """
        self.llm_service = llm_service
        self.onet_repository = onet_repository
        self.batch_size = batch_size
        self.candidates_per_role = candidates_per_role

    async def map_roles(self, roles: list[str]) -> list[RoleMappingResult]:
        """Map a list of role titles to O*NET occupations.

        Args:
            roles: List of role titles to map.

        Returns:
            List of RoleMappingResult objects.
        """
        if not roles:
            return []

        logger.info(f"Mapping {len(roles)} roles to O*NET occupations")

        # Get candidates for all roles
        candidates = await self._get_candidates(roles)

        # Chunk into batches
        batches = self._chunk_roles(roles, candidates)

        # Process each batch
        results = []
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i + 1}/{len(batches)}")
            batch_results = await self._process_batch(batch)
            results.extend(batch_results)

        return results

    async def _get_candidates(
        self,
        roles: list[str],
    ) -> dict[str, list[OnetOccupation]]:
        """Retrieve O*NET candidates for each role.

        Uses full-text search to find potential matches.

        Args:
            roles: List of role titles.

        Returns:
            Dict mapping role to list of candidate occupations.
        """
        candidates: dict[str, list[OnetOccupation]] = {}

        for role in roles:
            try:
                candidates[role] = await self.onet_repository.search_with_full_text(
                    query=role,
                    limit=self.candidates_per_role,
                )
            except Exception as e:
                logger.warning(f"Failed to get candidates for '{role}': {e}")
                candidates[role] = []

        return candidates

    def _chunk_roles(
        self,
        roles: list[str],
        candidates: dict[str, list[OnetOccupation]],
    ) -> list[list[tuple[str, list[OnetOccupation]]]]:
        """Chunk roles into batches for LLM processing.

        Args:
            roles: List of role titles.
            candidates: Dict mapping role to candidates.

        Returns:
            List of batches, each batch is a list of (role, candidates) tuples.
        """
        batches: list[list[tuple[str, list[OnetOccupation]]]] = []
        current_batch: list[tuple[str, list[OnetOccupation]]] = []

        for role in roles:
            current_batch.append((role, candidates.get(role, [])))
            if len(current_batch) >= self.batch_size:
                batches.append(current_batch)
                current_batch = []

        if current_batch:
            batches.append(current_batch)

        return batches

    async def _process_batch(
        self,
        batch: list[tuple[str, list[OnetOccupation]]],
    ) -> list[RoleMappingResult]:
        """Process a batch of roles through the LLM.

        Args:
            batch: List of (role, candidates) tuples.

        Returns:
            List of RoleMappingResult objects.
        """
        # Build prompt
        prompt = self._build_prompt(batch)

        try:
            # Call LLM
            response = await self.llm_service.generate_response(
                system_prompt=SYSTEM_PROMPT,
                user_message=prompt,
            )

            # Parse response
            return self._parse_response(response, batch)

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Return low-confidence fallbacks
            return self._create_fallback_results(batch, str(e))

    def _build_prompt(
        self,
        batch: list[tuple[str, list[OnetOccupation]]],
    ) -> str:
        """Build the user prompt for the LLM.

        Args:
            batch: List of (role, candidates) tuples.

        Returns:
            Formatted prompt string.
        """
        lines = []

        for i, (role, candidates) in enumerate(batch, 1):
            lines.append(f"Role {i}: \"{role}\"")
            lines.append("Candidates:")

            if candidates:
                for occ in candidates:
                    desc = (occ.description or "")[:200]
                    lines.append(f"  - {occ.code}: {occ.title} - {desc}")
            else:
                lines.append("  (No candidates found)")

            lines.append("")

        return "\n".join(lines)

    def _parse_response(
        self,
        response: str,
        batch: list[tuple[str, list[OnetOccupation]]],
    ) -> list[RoleMappingResult]:
        """Parse LLM response into RoleMappingResult objects.

        Args:
            response: LLM response text (should be JSON).
            batch: Original batch for fallback data.

        Returns:
            List of RoleMappingResult objects.
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]

            data = json.loads(json_str)

            results = []

            for item in data:
                role = item.get("role", "")
                onet_code = item.get("onet_code")
                onet_title = item.get("onet_title")
                confidence_str = item.get("confidence", "LOW")
                reasoning = item.get("reasoning", "")

                # Parse confidence tier
                try:
                    confidence = ConfidenceTier(confidence_str.upper())
                except ValueError:
                    confidence = ConfidenceTier.LOW

                results.append(RoleMappingResult(
                    source_role=role,
                    onet_code=onet_code,
                    onet_title=onet_title,
                    confidence=confidence,
                    reasoning=reasoning,
                ))

            return results

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._create_fallback_results(batch, f"Parse error: {e}")

    def _create_fallback_results(
        self,
        batch: list[tuple[str, list[OnetOccupation]]],
        error_msg: str,
    ) -> list[RoleMappingResult]:
        """Create low-confidence fallback results when LLM fails.

        Args:
            batch: Original batch.
            error_msg: Error message to include in reasoning.

        Returns:
            List of RoleMappingResult objects with LOW confidence.
        """
        results = []

        for role, candidates in batch:
            if candidates:
                # Use first candidate as fallback
                first = candidates[0]
                results.append(RoleMappingResult(
                    source_role=role,
                    onet_code=first.code,
                    onet_title=first.title,
                    confidence=ConfidenceTier.LOW,
                    reasoning=f"Fallback match - {error_msg}",
                ))
            else:
                results.append(RoleMappingResult(
                    source_role=role,
                    onet_code=None,
                    onet_title=None,
                    confidence=ConfidenceTier.LOW,
                    reasoning=f"No candidates found - {error_msg}",
                ))

        return results
