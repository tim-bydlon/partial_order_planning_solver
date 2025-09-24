"""
Integration tests for Phase 3: Natural Language Planning Agent

Tests the complete pipeline from natural language query to planning results.
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock
from pop_solver.mcp_client import MCPClient
from pop_solver.agent import PlanningAgent


class TestMCPClient:
    """Test MCP client STDIO communication"""

    @pytest.mark.asyncio
    async def test_mcp_client_initialization(self):
        """Test MCP client can connect to server"""
        client = MCPClient()
        await client.start()

        # Verify process is running
        assert client.process is not None
        assert client.process.returncode is None  # Process still running

        await client.close()
        assert client.process is None

    @pytest.mark.asyncio
    async def test_mcp_client_list_tools(self):
        """Test listing available MCP tools"""
        async with MCPClient() as client:
            tools = await client.list_tools()

            # Check both tools are available
            tool_names = [tool['name'] for tool in tools]
            assert 'apply_operator_tool' in tool_names
            assert 'create_plan_tool' in tool_names

    @pytest.mark.asyncio
    async def test_mcp_client_call_apply_operator(self):
        """Test calling apply_operator through MCP client"""
        async with MCPClient() as client:
            result = await client.call_tool("apply_operator_tool", {
                "start_conditions": ["On(Robot, Floor)", "Dry(Ladder)", "Dry(Ceiling)"],
                "operator": "climb-ladder",
                "problem_type": "robot"
            })

            assert isinstance(result, str)
            assert "climb-ladder" in result

    @pytest.mark.asyncio
    async def test_mcp_client_call_create_plan(self):
        """Test calling create_plan through MCP client"""
        async with MCPClient() as client:
            result = await client.call_tool("create_plan_tool", {
                "start_conditions": ["On(Robot, Floor)", "Dry(Ladder)", "Dry(Ceiling)"],
                "goal_conditions": ["Painted(Ceiling)"],
                "problem_type": "robot"
            })

            assert isinstance(result, str)
            assert "Painted(Ceiling)" in result

    @pytest.mark.asyncio
    async def test_mcp_client_error_handling(self):
        """Test MCP client handles errors gracefully"""
        async with MCPClient() as client:
            # Test with invalid operator
            result = await client.call_tool("apply_operator_tool", {
                "start_conditions": ["On(Robot, Floor)"],
                "operator": "invalid-operator",
                "problem_type": "robot"
            })

            assert isinstance(result, str)
            # Should get error message but not crash
            assert "Error" in result or "not found" in result.lower()


class TestPlanningAgent:
    """Test the planning agent with natural language processing"""

    @pytest.fixture
    def mock_api_key(self):
        """Provide mock API key for testing"""
        return "test-api-key"

    @pytest.mark.asyncio
    async def test_agent_parse_simple_goal(self, mock_api_key):
        """Test parsing simple goal query"""
        with patch.object(PlanningAgent, '__init__', lambda x, api_key: None):
            agent = PlanningAgent(api_key=mock_api_key)
            agent.api_key = mock_api_key
            agent.model = "claude-3-5-sonnet-20241022"

            # Mock Anthropic client
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='''```json
            {
                "problem_type": "robot",
                "current_state": ["On(Robot, Floor)", "Dry(Ladder)", "Dry(Ceiling)"],
                "goals": ["Painted(Ceiling)"],
                "query_type": "plan",
                "operator": null
            }
            ```''')]

            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            agent.client = mock_client

            parsed = await agent.parse_query("Help the robot paint the ceiling")

            assert parsed["problem_type"] == "robot"
            assert parsed["query_type"] == "plan"
            assert "Painted(Ceiling)" in parsed["goals"]
            assert parsed["operator"] is None

    @pytest.mark.asyncio
    async def test_agent_parse_operator_query(self, mock_api_key):
        """Test parsing operator application query"""
        with patch.object(PlanningAgent, '__init__', lambda x, api_key: None):
            agent = PlanningAgent(api_key=mock_api_key)
            agent.api_key = mock_api_key
            agent.model = "claude-3-5-sonnet-20241022"

            # Mock Anthropic client
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='''```json
            {
                "problem_type": "robot",
                "current_state": ["On(Robot, Floor)", "Dry(Ladder)", "Dry(Ceiling)"],
                "goals": [],
                "query_type": "operator",
                "operator": "climb-ladder"
            }
            ```''')]

            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            agent.client = mock_client

            parsed = await agent.parse_query("What happens if the robot climbs the ladder?")

            assert parsed["problem_type"] == "robot"
            assert parsed["query_type"] == "operator"
            assert parsed["operator"] == "climb-ladder"
            assert len(parsed["goals"]) == 0

    @pytest.mark.asyncio
    async def test_agent_format_response(self, mock_api_key):
        """Test formatting planning results"""
        with patch.object(PlanningAgent, '__init__', lambda x, api_key: None):
            agent = PlanningAgent(api_key=mock_api_key)
            agent.api_key = mock_api_key
            agent.model = "claude-3-5-sonnet-20241022"

            # Mock Anthropic client
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="""To paint the ceiling, the robot needs to:
1. Climb the ladder (from floor to ladder)
2. Paint the ceiling (while on the ladder)

The robot will end up on the ladder with the ceiling painted.""")]

            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            agent.client = mock_client

            plan_result = "[Plan with climb-ladder and paint-ceiling]"
            formatted = await agent.format_response(plan_result, "plan")

            assert "climb" in formatted.lower() or "ladder" in formatted.lower()
            assert "paint" in formatted.lower() or "ceiling" in formatted.lower()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="Requires ANTHROPIC_API_KEY")
    async def test_agent_end_to_end_with_real_api(self):
        """Test complete agent pipeline with real API (if key available)"""
        agent = PlanningAgent()

        result = await agent.process_query("Help the robot paint the ceiling")

        assert result["success"] is True
        assert "query" in result
        assert "parsed" in result
        assert "raw_result" in result
        assert "formatted_result" in result
        assert len(result["formatted_result"]) > 0


class TestAPIEndpoint:
    """Test the /solve FastAPI endpoint"""

    @pytest.mark.asyncio
    async def test_solve_endpoint_structure(self):
        """Test /solve endpoint request/response structure"""
        from fastapi.testclient import TestClient
        from pop_solver.app import app

        client = TestClient(app)

        # Test with missing API key (should fail gracefully)
        response = client.post("/solve", json={
            "query": "Help the robot paint the ceiling"
        })

        # Should get 400 error for missing API key
        assert response.status_code == 400
        assert "ANTHROPIC_API_KEY" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_solve_endpoint_with_mock(self):
        """Test /solve endpoint with mocked agent"""
        from fastapi.testclient import TestClient
        from pop_solver.app import app

        with patch('pop_solver.agent.PlanningAgent') as MockAgent:
            # Mock the agent
            mock_agent_instance = AsyncMock()
            mock_agent_instance.process_query = AsyncMock(return_value={
                "query": "Help the robot paint the ceiling",
                "success": True,
                "formatted_result": "The robot should climb the ladder and paint the ceiling.",
                "parsed": {"problem_type": "robot", "goals": ["Painted(Ceiling)"]},
                "raw_result": "[Plan details]"
            })
            MockAgent.return_value = mock_agent_instance

            client = TestClient(app)
            response = client.post("/solve", json={
                "query": "Help the robot paint the ceiling",
                "api_key": "test-key"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["query"] == "Help the robot paint the ceiling"
            assert "climb" in data["result"].lower() or "ladder" in data["result"].lower()


class TestIntegration:
    """Full integration tests"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="Requires ANTHROPIC_API_KEY")
    async def test_full_pipeline_integration(self):
        """Test complete pipeline from query to result"""
        from fastapi.testclient import TestClient
        from pop_solver.app import app

        client = TestClient(app)

        # Test multiple query types
        test_queries = [
            "Help the robot paint the ceiling",
            "What happens if the robot climbs the ladder?",
            "The robot needs to paint both the ceiling and the ladder"
        ]

        for query in test_queries:
            response = client.post("/solve", json={
                "query": query
            })

            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert len(data["result"]) > 0
                assert data["query"] == query