"""Integration tests for O*NET and Anthropic API connectivity.

These tests verify real API connectivity and are skipped if API keys
are not properly configured in the environment.

To run these tests:
1. Set ONET_API_KEY and ANTHROPIC_API_KEY environment variables
2. Run: pytest tests/integration/test_api_integration.py -v -m integration
"""

import os
from uuid import uuid4

import pytest

# Check if API keys are configured
ONET_API_KEY = os.getenv("ONET_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

ONET_KEY_PLACEHOLDER = "your_onet_api_key_here"
ANTHROPIC_KEY_PLACEHOLDER = "your_anthropic_api_key_here"


def is_onet_key_configured() -> bool:
    """Check if O*NET API key is properly configured."""
    return bool(ONET_API_KEY) and ONET_API_KEY != ONET_KEY_PLACEHOLDER


def is_anthropic_key_configured() -> bool:
    """Check if Anthropic API key is properly configured."""
    return bool(ANTHROPIC_API_KEY) and ANTHROPIC_API_KEY != ANTHROPIC_KEY_PLACEHOLDER


# =============================================================================
# O*NET API Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_onet_key_configured(),
    reason="O*NET API key not configured (set ONET_API_KEY env var)",
)
async def test_onet_api_search_occupations():
    """Test O*NET API connectivity by searching for occupations."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient

    settings = get_settings()
    client = OnetApiClient(settings)

    # Search for a common term that should return results
    results = await client.search_occupations("software")

    # Verify we got results
    assert isinstance(results, list)
    assert len(results) > 0, "Expected at least one occupation result for 'software'"

    # Verify response structure
    first_result = results[0]
    assert "code" in first_result, "Occupation should have 'code' field"
    assert "title" in first_result, "Occupation should have 'title' field"

    # Verify the code format (O*NET codes are like "15-1252.00")
    code = first_result["code"]
    assert isinstance(code, str)
    assert len(code) > 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_onet_key_configured(),
    reason="O*NET API key not configured (set ONET_API_KEY env var)",
)
async def test_onet_api_get_occupation_details():
    """Test O*NET API can retrieve occupation details."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient

    settings = get_settings()
    client = OnetApiClient(settings)

    # Use a well-known occupation code (Software Developer)
    occupation_code = "15-1252.00"
    result = await client.get_occupation(occupation_code)

    # Verify we got a result
    assert result is not None, f"Expected occupation details for code {occupation_code}"
    assert isinstance(result, dict)

    # Verify expected fields are present
    assert "code" in result, "Occupation details should have 'code' field"
    assert "title" in result, "Occupation details should have 'title' field"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_onet_key_configured(),
    reason="O*NET API key not configured (set ONET_API_KEY env var)",
)
async def test_onet_api_get_work_activities():
    """Test O*NET API can retrieve work activities for an occupation."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient

    settings = get_settings()
    client = OnetApiClient(settings)

    # Use a well-known occupation code (Software Developer)
    occupation_code = "15-1252.00"
    activities = await client.get_work_activities(occupation_code)

    # Verify we got results
    assert isinstance(activities, list)
    assert len(activities) > 0, f"Expected work activities for code {occupation_code}"

    # Verify response structure
    first_activity = activities[0]
    assert "id" in first_activity, "Activity should have 'id' field"
    assert "name" in first_activity, "Activity should have 'name' field"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_onet_key_configured(),
    reason="O*NET API key not configured (set ONET_API_KEY env var)",
)
async def test_onet_api_get_tasks():
    """Test O*NET API can retrieve tasks for an occupation."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient

    settings = get_settings()
    client = OnetApiClient(settings)

    # Use a well-known occupation code (Software Developer)
    occupation_code = "15-1252.00"
    tasks = await client.get_tasks(occupation_code)

    # Verify we got results
    assert isinstance(tasks, list)
    assert len(tasks) > 0, f"Expected tasks for code {occupation_code}"

    # Verify response structure (v2 API uses 'title' instead of 'statement')
    first_task = tasks[0]
    assert "id" in first_task, "Task should have 'id' field"
    assert "title" in first_task, "Task should have 'title' field"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_onet_key_configured(),
    reason="O*NET API key not configured (set ONET_API_KEY env var)",
)
async def test_onet_api_nonexistent_occupation():
    """Test O*NET API returns None for non-existent occupation codes."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient

    settings = get_settings()
    client = OnetApiClient(settings)

    # Use an invalid occupation code
    invalid_code = "99-9999.99"
    result = await client.get_occupation(invalid_code)

    # Should return None for non-existent code
    assert result is None, f"Expected None for invalid code {invalid_code}"


# =============================================================================
# Anthropic API Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_anthropic_key_configured(),
    reason="Anthropic API key not configured (set ANTHROPIC_API_KEY env var)",
)
async def test_anthropic_api_generate_response():
    """Test Anthropic API connectivity with a simple generation request."""
    from app.config import get_settings
    from app.services.llm_service import LLMService

    settings = get_settings()
    llm_service = LLMService(settings=settings, max_tokens=100, temperature=0.0)

    # Generate a simple response
    response = await llm_service.generate_response(
        system_prompt="You are a helpful assistant. Respond concisely.",
        user_message="Say 'Hello, integration test!' and nothing else.",
    )

    # Verify we got a response
    assert isinstance(response, str)
    assert len(response) > 0, "Expected non-empty response from LLM"

    # The response should contain our expected phrase (case-insensitive check)
    assert "hello" in response.lower(), "Response should contain 'hello'"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_anthropic_key_configured(),
    reason="Anthropic API key not configured (set ANTHROPIC_API_KEY env var)",
)
async def test_anthropic_api_with_conversation_history():
    """Test Anthropic API handles conversation history correctly."""
    from app.config import get_settings
    from app.services.llm_service import LLMService

    settings = get_settings()
    llm_service = LLMService(settings=settings, max_tokens=100, temperature=0.0)

    # Create a conversation with history
    history = [
        {"role": "user", "content": "My name is IntegrationTest."},
        {"role": "assistant", "content": "Nice to meet you, IntegrationTest!"},
    ]

    response = await llm_service.generate_response(
        system_prompt="You are a helpful assistant. Respond concisely.",
        user_message="What is my name?",
        conversation_history=history,
    )

    # Verify the response references the name from history
    assert isinstance(response, str)
    assert len(response) > 0
    assert "integrationtest" in response.lower(), (
        "Response should reference the name 'IntegrationTest' from conversation history"
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_anthropic_key_configured(),
    reason="Anthropic API key not configured (set ANTHROPIC_API_KEY env var)",
)
async def test_anthropic_api_streaming():
    """Test Anthropic API streaming response functionality."""
    from app.config import get_settings
    from app.services.llm_service import LLMService

    settings = get_settings()
    llm_service = LLMService(settings=settings, max_tokens=100, temperature=0.0)

    # Collect streamed chunks
    chunks: list[str] = []
    async for chunk in llm_service.stream_response(
        system_prompt="You are a helpful assistant. Respond concisely.",
        user_message="Count from 1 to 5, separated by commas.",
    ):
        chunks.append(chunk)

    # Verify we received chunks
    assert len(chunks) > 0, "Expected at least one streamed chunk"

    # Join chunks and verify content
    full_response = "".join(chunks)
    assert len(full_response) > 0, "Expected non-empty streamed response"

    # The response should contain numbers
    assert any(str(n) in full_response for n in range(1, 6)), (
        "Response should contain numbers 1-5"
    )


# =============================================================================
# End-to-End ChatService Integration Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_anthropic_key_configured(),
    reason="Anthropic API key not configured (set ANTHROPIC_API_KEY env var)",
)
async def test_chat_service_send_message():
    """Test ChatService end-to-end with real LLM API."""
    from app.services.chat_service import ChatService
    from app.services.context_service import ContextService
    from app.config import get_settings
    from app.services.llm_service import LLMService

    settings = get_settings()
    llm_service = LLMService(settings=settings, max_tokens=200, temperature=0.7)
    context_service = ContextService()

    chat_service = ChatService(
        llm_service=llm_service,
        context_service=context_service,
    )

    # Send a message through the chat service
    session_id = uuid4()
    result = await chat_service.send_message(
        session_id=session_id,
        message="Hello, I need help uploading my organizational data.",
        current_step=1,
    )

    # Verify response structure
    assert isinstance(result, dict)
    assert "response" in result, "Result should have 'response' key"
    assert "quick_actions" in result, "Result should have 'quick_actions' key"

    # Verify response content
    response = result["response"]
    assert isinstance(response, str)
    assert len(response) > 0, "Expected non-empty response"

    # Verify quick actions
    quick_actions = result["quick_actions"]
    assert isinstance(quick_actions, list)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_anthropic_key_configured(),
    reason="Anthropic API key not configured (set ANTHROPIC_API_KEY env var)",
)
async def test_chat_service_different_steps():
    """Test ChatService returns appropriate quick actions for different steps."""
    from app.services.chat_service import ChatService
    from app.services.context_service import ContextService
    from app.config import get_settings
    from app.services.llm_service import LLMService

    settings = get_settings()
    llm_service = LLMService(settings=settings, max_tokens=100, temperature=0.7)
    context_service = ContextService()

    chat_service = ChatService(
        llm_service=llm_service,
        context_service=context_service,
    )

    session_id = uuid4()

    # Test each step has appropriate quick actions
    for step in range(1, 6):
        result = await chat_service.send_message(
            session_id=session_id,
            message=f"Help me with step {step}",
            current_step=step,
        )

        assert "quick_actions" in result
        quick_actions = result["quick_actions"]
        assert isinstance(quick_actions, list)

        # Each step should have at least one quick action defined
        assert len(quick_actions) >= 1, f"Step {step} should have quick actions"


# =============================================================================
# Combined O*NET + LLM Integration Test
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not (is_onet_key_configured() and is_anthropic_key_configured()),
    reason="Both O*NET and Anthropic API keys required for this test",
)
async def test_onet_data_with_llm_analysis():
    """Test fetching O*NET data and analyzing it with the LLM."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient
    from app.services.llm_service import LLMService

    settings = get_settings()
    onet_client = OnetApiClient(settings)
    llm_service = LLMService(settings=settings, max_tokens=200, temperature=0.0)

    # Fetch occupation data from O*NET
    occupation_code = "15-1252.00"
    occupation = await onet_client.get_occupation(occupation_code)
    tasks = await onet_client.get_tasks(occupation_code)

    assert occupation is not None
    assert len(tasks) > 0

    # Use LLM to analyze the occupation data
    occupation_title = occupation.get("title", "Software Developer")
    task_statements = [t.get("statement", "") for t in tasks[:3]]

    prompt = f"""Analyze the following occupation and tasks for AI automation potential:

Occupation: {occupation_title}
Sample Tasks:
- {task_statements[0] if len(task_statements) > 0 else 'N/A'}
- {task_statements[1] if len(task_statements) > 1 else 'N/A'}
- {task_statements[2] if len(task_statements) > 2 else 'N/A'}

Briefly identify one task that could benefit from AI automation."""

    response = await llm_service.generate_response(
        system_prompt="You are an expert in AI automation opportunities. Be concise.",
        user_message=prompt,
    )

    # Verify we got an analysis
    assert isinstance(response, str)
    assert len(response) > 0, "Expected LLM analysis of O*NET data"


# =============================================================================
# Error Handling Tests (require valid API keys to test error conditions)
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_onet_key_configured(),
    reason="O*NET API key not configured (set ONET_API_KEY env var)",
)
async def test_onet_api_empty_search():
    """Test O*NET API handles searches with no results gracefully."""
    from app.config import get_settings
    from app.services.onet_client import OnetApiClient

    settings = get_settings()
    client = OnetApiClient(settings)

    # Search for a term unlikely to have results
    results = await client.search_occupations("xyznonexistentoccupation123")

    # Should return empty list, not raise an error
    assert isinstance(results, list)
    # May be empty or have results depending on O*NET's fuzzy matching
