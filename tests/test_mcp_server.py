"""
Test suite for MCP server integration

Tests MCP server functionality, tool registration, and ensures MCP tools
return identical outputs to direct function calls.
"""

import pytest
import asyncio
from pop_solver.mcp_server import mcp, apply_operator_tool, create_plan_tool
from pop_solver.planning.planning_solving_functions import apply_operator, create_plan


class TestMCPServerTools:
    """Test MCP server tool functionality and output parity with direct functions"""

    @pytest.mark.asyncio
    async def test_apply_operator_tool_climb_ladder(self):
        """Test apply_operator MCP tool returns identical output to direct function"""
        start_conditions = ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        operator = 'climb-ladder'
        problem_type = 'robot'

        # Get results from both MCP tool and direct function
        mcp_result = await apply_operator_tool(start_conditions, operator, problem_type)
        direct_result = apply_operator(start_conditions, operator, problem_type)

        # Results should be identical
        assert mcp_result == direct_result

    @pytest.mark.asyncio
    async def test_apply_operator_tool_invalid_operator(self):
        """Test apply_operator MCP tool error handling for invalid operator"""
        start_conditions = ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        operator = 'invalid-operator'
        problem_type = 'robot'

        # Get results from both MCP tool and direct function
        mcp_result = await apply_operator_tool(start_conditions, operator, problem_type)
        direct_result = apply_operator(start_conditions, operator, problem_type)

        # Results should be identical
        assert mcp_result == direct_result

    @pytest.mark.asyncio
    async def test_apply_operator_tool_failed_precondition(self):
        """Test apply_operator MCP tool error handling for failed preconditions"""
        start_conditions = ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        operator = 'paint-ceiling'  # Requires robot on ladder
        problem_type = 'robot'

        # Get results from both MCP tool and direct function
        mcp_result = await apply_operator_tool(start_conditions, operator, problem_type)
        direct_result = apply_operator(start_conditions, operator, problem_type)

        # Results should be identical
        assert mcp_result == direct_result

    @pytest.mark.asyncio
    async def test_apply_operator_tool_blockworld_error(self):
        """Test apply_operator MCP tool error handling for blockworld problem type"""
        start_conditions = ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        operator = 'climb-ladder'
        problem_type = 'blockworld'

        # MCP tool should handle ValueError and return error string
        mcp_result = await apply_operator_tool(start_conditions, operator, problem_type)

        # Should return blockworld error message
        assert mcp_result == "Error: Blockworld planner not implemented"

    @pytest.mark.asyncio
    async def test_create_plan_tool_paint_ceiling(self):
        """Test create_plan MCP tool returns identical output to direct function"""
        start_conditions = ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        goal_conditions = ['Painted(Ceiling)']
        problem_type = 'robot'

        # Get results from both MCP tool and direct function
        mcp_result = await create_plan_tool(start_conditions, goal_conditions, problem_type)
        direct_result = create_plan(start_conditions, goal_conditions, problem_type)

        # Results should be identical
        assert mcp_result == direct_result

    @pytest.mark.asyncio
    async def test_create_plan_tool_multiple_goals(self):
        """Test create_plan MCP tool with multiple goals"""
        start_conditions = ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        goal_conditions = ['Painted(Ceiling)', 'Painted(Ladder)']
        problem_type = 'robot'

        # Get results from both MCP tool and direct function
        mcp_result = await create_plan_tool(start_conditions, goal_conditions, problem_type)
        direct_result = create_plan(start_conditions, goal_conditions, problem_type)

        # Results should be identical
        assert mcp_result == direct_result

    @pytest.mark.asyncio
    async def test_create_plan_tool_invalid_start_conditions(self):
        """Test create_plan MCP tool error handling for invalid start conditions"""
        start_conditions = ['Invalid(Condition)']
        goal_conditions = ['Painted(Ceiling)']
        problem_type = 'robot'

        # Get results from both MCP tool and direct function
        mcp_result = await create_plan_tool(start_conditions, goal_conditions, problem_type)
        direct_result = create_plan(start_conditions, goal_conditions, problem_type)

        # Results should be identical
        assert mcp_result == direct_result

    @pytest.mark.asyncio
    async def test_create_plan_tool_invalid_goal_conditions(self):
        """Test create_plan MCP tool handles LookupError for invalid goals"""
        start_conditions = ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        goal_conditions = ['Invalid(Goal)']
        problem_type = 'robot'

        # MCP tool should catch LookupError and return error string
        mcp_result = await create_plan_tool(start_conditions, goal_conditions, problem_type)

        # Should start with "Error:" since LookupError is converted
        assert mcp_result.startswith("Error:")
        assert "No operator found with postconditions matching the goal condition 'Invalid(Goal)'" in mcp_result

    @pytest.mark.asyncio
    async def test_create_plan_tool_blockworld_error(self):
        """Test create_plan MCP tool error handling for blockworld problem type"""
        start_conditions = ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        goal_conditions = ['Painted(Ceiling)']
        problem_type = 'blockworld'

        # Get results from both MCP tool and direct function
        mcp_result = await create_plan_tool(start_conditions, goal_conditions, problem_type)
        direct_result = create_plan(start_conditions, goal_conditions, problem_type)

        # Results should be identical
        assert mcp_result == direct_result


class TestMCPServerStructure:
    """Test MCP server structure and tool registration"""

    def test_mcp_server_instance(self):
        """Test that MCP server is properly instantiated"""
        assert mcp is not None
        assert hasattr(mcp, 'run')

    @pytest.mark.asyncio
    async def test_tools_are_registered(self):
        """Test that both tools are registered with the MCP server"""
        # Get list of registered tools
        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        # Both tools should be registered
        assert 'apply_operator_tool' in tool_names
        assert 'create_plan_tool' in tool_names

    @pytest.mark.asyncio
    async def test_apply_operator_tool_schema(self):
        """Test apply_operator_tool has proper schema definition"""
        tools = await mcp.list_tools()
        apply_tool = next(tool for tool in tools if tool.name == 'apply_operator_tool')

        # Check tool has required fields
        assert hasattr(apply_tool, 'description')
        assert hasattr(apply_tool, 'inputSchema')

        # Check parameters are defined
        properties = apply_tool.inputSchema['properties']
        assert 'start_conditions' in properties
        assert 'operator' in properties
        assert 'problem_type' in properties

    @pytest.mark.asyncio
    async def test_create_plan_tool_schema(self):
        """Test create_plan_tool has proper schema definition"""
        tools = await mcp.list_tools()
        plan_tool = next(tool for tool in tools if tool.name == 'create_plan_tool')

        # Check tool has required fields
        assert hasattr(plan_tool, 'description')
        assert hasattr(plan_tool, 'inputSchema')

        # Check parameters are defined
        properties = plan_tool.inputSchema['properties']
        assert 'start_conditions' in properties
        assert 'goal_conditions' in properties
        assert 'problem_type' in properties


class TestErrorHandling:
    """Test comprehensive error handling in MCP tools"""

    @pytest.mark.asyncio
    async def test_apply_operator_tool_exception_handling(self):
        """Test apply_operator_tool handles unexpected exceptions"""
        # Test with malformed input that might cause unexpected errors
        start_conditions = []  # Empty conditions
        operator = 'climb-ladder'
        problem_type = 'robot'

        mcp_result = await apply_operator_tool(start_conditions, operator, problem_type)

        # Should return some error message, not raise exception
        assert isinstance(mcp_result, str)
        assert mcp_result.startswith("Error:")

    @pytest.mark.asyncio
    async def test_create_plan_tool_exception_handling(self):
        """Test create_plan_tool handles unexpected exceptions"""
        # Test with malformed input that might cause unexpected errors
        start_conditions = []  # Empty conditions
        goal_conditions = []  # Empty goals
        problem_type = 'robot'

        mcp_result = await create_plan_tool(start_conditions, goal_conditions, problem_type)

        # Should return some error message, not raise exception
        assert isinstance(mcp_result, str)
        assert mcp_result.startswith("Error:")