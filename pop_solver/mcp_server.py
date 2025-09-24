"""
MCP Server for Partial Order Planning Solver

Exposes planning functions as MCP tools via STDIO transport for local agent integration.
"""

from typing import List
from mcp.server.fastmcp import FastMCP
from pop_solver.planning.planning_solving_functions import apply_operator, create_plan

# Initialize FastMCP server
mcp = FastMCP("partial-order-planning-solver")


@mcp.tool()
async def apply_operator_tool(
    start_conditions: List[str],
    operator: str,
    problem_type: str = 'robot'
) -> str:
    """
    Apply a planning operator to a given state in the robot painting problem.

    Available operators for robot problem:
    - climb-ladder: Robot climbs from floor to ladder (requires dry ladder)
    - descend-ladder: Robot descends from ladder to floor (requires dry ladder)
    - paint-ceiling: Paint the ceiling (requires robot on ladder)
    - paint-ladder: Paint the ladder (requires robot on floor)

    Args:
        start_conditions: List of state conditions like ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        operator: Name of operator to apply (e.g., 'climb-ladder')
        problem_type: Type of planning problem ('robot' or 'blockworld'), defaults to 'robot'

    Returns:
        String describing the result of applying the operator or error message

    Note: Currently has known bug where result state equals start state, but precondition validation works correctly.
    """
    try:
        result = apply_operator(start_conditions, operator, problem_type)
        return result
    except ValueError as e:
        # Handle blockworld not implemented and other validation errors
        if "Blockworld planner not implemented" in str(e):
            return f"Error: Blockworld planner not implemented"
        return str(e)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def create_plan_tool(
    start_conditions: List[str],
    goal_conditions: List[str],
    problem_type: str = 'robot'
) -> str:
    """
    Create a sequential plan to achieve goal conditions from start conditions.

    Supports multiple goals and creates sequential plans with intermediate steps.
    Available goal conditions for robot problem:
    - Painted(Ceiling): Paint the ceiling
    - Painted(Ladder): Paint the ladder

    Args:
        start_conditions: List of initial state conditions like ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']
        goal_conditions: List of desired goal conditions like ['Painted(Ceiling)']
        problem_type: Type of planning problem ('robot' or 'blockworld'), defaults to 'robot'

    Returns:
        String representation of plan(s) with operator and state steps, or error message

    Raises:
        LookupError: When goal conditions cannot be achieved (converted to error string)
    """
    try:
        result = create_plan(start_conditions, goal_conditions, problem_type)
        return result
    except LookupError as e:
        # Convert LookupError exceptions to error response strings
        return f"Error: {str(e)}"
    except ValueError as e:
        # Handle blockworld not implemented and other validation errors
        if "Blockworld planner not implemented" in str(e):
            return "Error: Blockworld planner not implemented"
        return str(e)
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # Start the MCP server with STDIO transport for local container execution
    mcp.run(transport='stdio')