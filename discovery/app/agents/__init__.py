"""Agents module for the Discovery service."""
from app.agents.base import BaseSubagent
from app.agents.upload_agent import UploadSubagent

__all__ = ["BaseSubagent", "UploadSubagent"]
