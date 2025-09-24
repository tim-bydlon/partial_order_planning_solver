"""
MCP Client for communication with local planning server

Handles STDIO-based communication with the MCP server subprocess.
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path


class MCPClient:
    """Client for communicating with MCP server via STDIO transport"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._request_id = 0

    async def start(self):
        """Start the MCP server subprocess and establish STDIO communication"""
        # Get the path to the MCP server script
        server_path = Path(__file__).parent / "mcp_server.py"

        # Start the MCP server as a subprocess
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, str(server_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Initialize the connection
        await self._initialize_connection()

    async def _initialize_connection(self):
        """Initialize the JSONRPC connection with the server"""
        # Send initialize request
        response = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "pop-solver-client",
                "version": "0.1.0"
            }
        })

        if "error" in response:
            raise ConnectionError(f"Failed to initialize MCP connection: {response['error']}")

        # Mark as initialized
        await self._send_notification("notifications/initialized", {})

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSONRPC request and wait for response"""
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._request_id
        }

        # Send request
        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode())
        await self.process.stdin.drain()

        # Read response
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode())

        # Handle response
        if response.get("id") != self._request_id:
            # This might be a notification or different response, keep reading
            while response.get("id") != self._request_id:
                response_line = await self.process.stdout.readline()
                if not response_line:
                    raise ConnectionError("MCP server closed connection")
                response = json.loads(response_line.decode())

        return response

    async def _send_notification(self, method: str, params: Dict[str, Any]):
        """Send a JSONRPC notification (no response expected)"""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        notification_str = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_str.encode())
        await self.process.stdin.drain()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool and return the result"""
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        if "error" in response:
            raise RuntimeError(f"Tool call failed: {response['error']}")

        # Extract the content from the response
        result = response.get("result", {})
        content = result.get("content", [])

        # For text responses, extract the text content
        if content and isinstance(content, list) and content[0].get("type") == "text":
            return content[0].get("text", "")

        return content

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server"""
        response = await self._send_request("tools/list", {})

        if "error" in response:
            raise RuntimeError(f"Failed to list tools: {response['error']}")

        return response.get("result", {}).get("tools", [])

    async def close(self):
        """Close the connection and terminate the subprocess"""
        if self.process:
            # Send close notification
            try:
                await self._send_notification("notifications/cancelled", {})
            except:
                pass  # Server might already be closing

            # Terminate the process
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

            self.process = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


async def test_mcp_client():
    """Test function to verify MCP client functionality"""
    async with MCPClient() as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool['name'] for tool in tools]}")

        # Test apply_operator
        result = await client.call_tool("apply_operator_tool", {
            "start_conditions": ["On(Robot, Floor)", "Dry(Ladder)", "Dry(Ceiling)"],
            "operator": "climb-ladder",
            "problem_type": "robot"
        })
        print(f"Apply operator result: {result}")

        # Test create_plan
        result = await client.call_tool("create_plan_tool", {
            "start_conditions": ["On(Robot, Floor)", "Dry(Ladder)", "Dry(Ceiling)"],
            "goal_conditions": ["Painted(Ceiling)"],
            "problem_type": "robot"
        })
        print(f"Create plan result: {result}")


if __name__ == "__main__":
    # Run test when module is executed directly
    asyncio.run(test_mcp_client())