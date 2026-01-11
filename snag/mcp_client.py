"""MCP client for Z.AI vision server communication."""

import json
import os
import subprocess
import sys
import threading
from typing import Any, Optional


class MCPError(Exception):
    """Error during MCP communication."""

    pass


class MCPClient:
    """Minimal MCP client for stdio-based servers."""

    def __init__(
        self, command: list[str], env: dict[str, str], timeout: int = 60
    ) -> None:
        """Initialize MCP client.

        Args:
            command: Command to spawn MCP server (e.g., ["npx", "-y", "@z_ai/mcp-server"])
            env: Environment variables to set (e.g., {"Z_AI_API_KEY": "...", "Z_AI_MODE": "ZAI"})
            timeout: Timeout in seconds for operations
        """
        self.command = command
        self.env = env
        self.timeout = timeout
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0

    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    def _send(self, message: dict) -> None:
        """Send JSON message to MCP server."""
        if not self._process or not self._process.stdin:
            raise MCPError("MCP server not connected")
        line = json.dumps(message) + "\n"
        self._process.stdin.write(line)
        self._process.stdin.flush()

    def _recv(self) -> dict:
        """Receive JSON message from MCP server with timeout."""
        if not self._process or not self._process.stdout:
            raise MCPError("MCP server not connected")

        result: dict = {}
        error: Optional[str] = None

        def read_line():
            nonlocal result, error
            try:
                line = self._process.stdout.readline()
                if not line:
                    error = "MCP server closed connection"
                    return
                result = json.loads(line.strip())
            except json.JSONDecodeError as e:
                error = f"Invalid JSON from MCP server: {e}"
            except Exception as e:
                error = f"Read error: {e}"

        # Use threading for timeout (works on all platforms)
        thread = threading.Thread(target=read_line)
        thread.start()
        thread.join(timeout=self.timeout)

        if thread.is_alive():
            # Timeout - kill process
            self._kill_process()
            raise MCPError(f"MCP server did not respond within {self.timeout}s")

        if error:
            raise MCPError(error)

        return result

    def _send_request(self, method: str, params: Optional[dict] = None) -> dict:
        """Send JSON-RPC request and wait for response."""
        request: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._next_id(),
        }
        if params:
            request["params"] = params

        self._send(request)
        response = self._recv()

        if "error" in response:
            error = response["error"]
            msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            raise MCPError(f"MCP error: {msg}")

        return response.get("result", {})

    def _send_notification(self, method: str, params: Optional[dict] = None) -> None:
        """Send JSON-RPC notification (no response expected)."""
        notification: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            notification["params"] = params

        self._send(notification)

    def _kill_process(self) -> None:
        """Kill the MCP server process."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None

    def connect(self) -> None:
        """Start MCP server process and perform initialization handshake."""
        # Build environment
        full_env = os.environ.copy()
        full_env.update(self.env)

        try:
            self._process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=full_env,
                text=True,
                bufsize=1,  # Line buffered
            )
        except FileNotFoundError as e:
            raise MCPError(f"Failed to start MCP server: {e}")
        except Exception as e:
            raise MCPError(f"Failed to start MCP server: {e}")

        # Perform initialization handshake
        try:
            self._send_request("initialize", {
                "protocolVersion": "0.1.0",
                "capabilities": {},
                "clientInfo": {"name": "snag", "version": "0.1.0"},
            })

            # Send initialized notification
            self._send_notification("notifications/initialized")

        except MCPError:
            self._kill_process()
            raise

    def disconnect(self) -> None:
        """Gracefully terminate MCP server process."""
        self._kill_process()

    def call_tool(self, name: str, arguments: dict) -> str:
        """Call an MCP tool and return the result text.

        Args:
            name: Tool name (e.g., "image_analysis")
            arguments: Tool arguments

        Returns:
            Text result from the tool
        """
        result = self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })

        # Extract text from content array
        content = result.get("content", [])
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(item.get("text", ""))
            return "\n".join(texts)
        elif isinstance(content, str):
            return content

        return str(result)

    def __enter__(self) -> "MCPClient":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        self.disconnect()
        return False
