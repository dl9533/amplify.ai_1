"""Enums for the Discovery service."""
from enum import Enum


class DiscoveryStep(str, Enum):
    """Enumeration of steps in the discovery wizard workflow.

    The discovery process follows a sequential wizard pattern:
    1. UPLOAD - User uploads organizational data file
    2. MAP_ROLES - Map uploaded columns to O*NET roles
    3. SELECT_ACTIVITIES - Select relevant work activities
    4. ANALYZE - Analyze automation opportunities
    5. ROADMAP - Generate implementation roadmap
    """

    UPLOAD = "upload"
    MAP_ROLES = "map_roles"
    SELECT_ACTIVITIES = "select_activities"
    ANALYZE = "analyze"
    ROADMAP = "roadmap"
