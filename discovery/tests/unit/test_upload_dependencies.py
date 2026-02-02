# discovery/tests/unit/test_upload_dependencies.py
"""Unit tests for upload dependencies."""
import pytest


def test_get_s3_client_exists():
    """Test get_s3_client dependency exists."""
    from app.dependencies import get_s3_client
    assert get_s3_client is not None


def test_get_file_parser_exists():
    """Test get_file_parser dependency exists."""
    from app.dependencies import get_file_parser
    assert get_file_parser is not None


def test_get_upload_service_dep_exists():
    """Test get_upload_service_dep dependency exists."""
    from app.dependencies import get_upload_service_dep
    assert get_upload_service_dep is not None


def test_s3_client_returns_instance():
    """Test get_s3_client returns S3Client instance."""
    from app.dependencies import get_s3_client
    from app.services.s3_client import S3Client

    client = get_s3_client()
    assert isinstance(client, S3Client)


def test_file_parser_returns_instance():
    """Test get_file_parser returns FileParser instance."""
    from app.dependencies import get_file_parser
    from app.services.file_parser import FileParser

    parser = get_file_parser()
    assert isinstance(parser, FileParser)
