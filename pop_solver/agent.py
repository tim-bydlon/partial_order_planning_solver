"""
Planning Agent with Natural Language Processing

Uses Claude 3.5 Sonnet to understand natural language planning queries
and convert them to structured planning problems.
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from anthropic import AsyncAnthropic
from pop_solver.mcp_client import MCPClient


class PlanningAgent:
    """Agent that processes natural language planning queries using Claude Sonnet"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the agent with Anthropic client"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided or found in environment")

        self.client = AsyncAnthropic(api_key=self.api_key)
        # Using Claude Sonnet 4
        self.model = "claude-sonnet-4-20250514"

    async def parse_query(self, user_query: str) -> Dict[str, Any]:
        """Parse natural language query to extract planning elements"""
        system_prompt = """You are a planning problem analyzer for a robot painting system.

        The robot painting domain has these elements:
        - Locations: Floor, Ladder
        - Objects: Robot, Ladder, Ceiling
        - States: Dry/Wet (¬Dry), Painted/Unpainted
        - Actions: climb-ladder, descend-ladder, paint-ceiling, paint-ladder

        Valid state conditions:
        - On(Robot, Floor) or On(Robot, Ladder)
        - Dry(Ladder) or ¬Dry(Ladder)
        - Dry(Ceiling) or ¬Dry(Ceiling)
        - Painted(Ladder)
        - Painted(Ceiling)

        Extract the following from the user's query:
        1. problem_type: Always "robot" (blockworld not implemented)
        2. current_state: List of current conditions (if not specified, use defaults)
        3. goals: List of goal conditions
        4. query_type: "plan" (create full plan) or "operator" (single action)
        5. operator: If query_type is "operator", which operator to apply

        Default starting state if not specified:
        ["On(Robot, Floor)", "Dry(Ladder)", "Dry(Ceiling)"]

        Return a JSON object with these fields."""

        user_prompt = f"""Parse this planning query: "{user_query}"

        Return a JSON object with:
        - problem_type: "robot"
        - current_state: array of state conditions
        - goals: array of goal conditions (empty if just applying operator)
        - query_type: "plan" or "operator"
        - operator: operator name if query_type is "operator", null otherwise

        Examples:
        "Help the robot paint the ceiling" -> plan to achieve Painted(Ceiling)
        "The robot needs to paint both the ceiling and ladder" -> plan for multiple goals
        "What happens if the robot climbs the ladder?" -> apply climb-ladder operator
        "Robot is on the ladder, paint the ceiling" -> plan from non-default state"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text
        try:
            # Try to parse the response as JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError:
            # Fallback to a simple plan query
            return {
                "problem_type": "robot",
                "current_state": ["On(Robot, Floor)", "Dry(Ladder)", "Dry(Ceiling)"],
                "goals": ["Painted(Ceiling)"],
                "query_type": "plan",
                "operator": None
            }

    async def format_response(self, result: str, query_type: str) -> str:
        """Format planning results for human readability"""
        system_prompt = """You are a helpful assistant explaining robot planning results.
        Format the technical planning output into clear, conversational language.
        Be concise but informative. Use numbered steps for plans."""

        if query_type == "plan":
            user_prompt = f"""Convert this planning result to human-readable format:

            {result}

            Format as:
            1. A brief summary
            2. Numbered steps the robot should take
            3. The final state achieved

            Keep it clear and conversational."""
        else:
            user_prompt = f"""Convert this operator application result to human-readable format:

            {result}

            Explain what happened when the operator was applied."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.content[0].text

    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process a natural language query end-to-end"""
        # Parse the query
        parsed = await self.parse_query(user_query)

        # Connect to MCP server and execute
        async with MCPClient() as mcp_client:
            if parsed["query_type"] == "operator":
                # Apply single operator
                result = await mcp_client.call_tool("apply_operator_tool", {
                    "start_conditions": parsed["current_state"],
                    "operator": parsed["operator"],
                    "problem_type": parsed["problem_type"]
                })
            else:
                # Create plan
                result = await mcp_client.call_tool("create_plan_tool", {
                    "start_conditions": parsed["current_state"],
                    "goal_conditions": parsed["goals"],
                    "problem_type": parsed["problem_type"]
                })

        # Format the response
        formatted = await self.format_response(result, parsed["query_type"])

        return {
            "query": user_query,
            "parsed": parsed,
            "raw_result": result,
            "formatted_result": formatted,
            "success": not result.startswith("Error:")
        }


async def test_agent():
    """Test the planning agent with sample queries"""
    agent = PlanningAgent()

    test_queries = [
        "Help the robot paint the ceiling",
        "The robot needs to paint both the ceiling and the ladder",
        "What happens if the robot climbs the ladder?",
        "The robot is on the ladder, now paint the ceiling"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        try:
            result = await agent.process_query(query)
            print(f"Success: {result['success']}")
            print(f"Formatted Response:\n{result['formatted_result']}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_agent())