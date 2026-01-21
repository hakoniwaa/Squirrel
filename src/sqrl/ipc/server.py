"""JSON-RPC 2.0 server over Unix socket."""

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

log = structlog.get_logger()

# JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# Custom error codes (from INTERFACES.md)
PROJECT_NOT_INITIALIZED = -32001
DAEMON_NOT_RUNNING = -32002
LLM_ERROR = -32003
INVALID_PROJECT_ROOT = -32004
NO_MEMORIES_FOUND = -32005

Handler = Callable[[dict[str, Any]], Awaitable[Any]]


class IPCServer:
    """JSON-RPC 2.0 server over Unix socket."""

    def __init__(self, socket_path: str) -> None:
        self.socket_path = socket_path
        self.handlers: dict[str, Handler] = {}
        self.server: asyncio.Server | None = None

    def register(self, method: str, handler: Handler) -> None:
        """Register a method handler."""
        self.handlers[method] = handler

    async def start(self) -> None:
        """Start the server."""
        # Remove existing socket file
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        self.server = await asyncio.start_unix_server(
            self._handle_client,
            path=self.socket_path,
        )
        log.info("ipc_server_listening", socket=self.socket_path)

    async def stop(self) -> None:
        """Stop the server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle a client connection."""
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                response = await self._process_request(data)
                writer.write(response.encode() + b"\n")
                await writer.drain()
        except Exception as e:
            log.error("client_error", error=str(e))
        finally:
            writer.close()
            await writer.wait_closed()

    async def _process_request(self, data: bytes) -> str:
        """Process a JSON-RPC request."""
        try:
            request = json.loads(data.decode())
        except json.JSONDecodeError as e:
            return self._error_response(None, PARSE_ERROR, f"Parse error: {e}")

        # Validate request
        if not isinstance(request, dict):
            return self._error_response(None, INVALID_REQUEST, "Invalid request")

        jsonrpc = request.get("jsonrpc")
        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")

        if jsonrpc != "2.0":
            return self._error_response(req_id, INVALID_REQUEST, "Invalid JSON-RPC version")

        if not method or not isinstance(method, str):
            return self._error_response(req_id, INVALID_REQUEST, "Missing method")

        # Find handler
        handler = self.handlers.get(method)
        if not handler:
            return self._error_response(req_id, METHOD_NOT_FOUND, f"Method not found: {method}")

        # Execute handler
        try:
            result = await handler(params)
            return self._success_response(req_id, result)
        except ValueError as e:
            return self._error_response(req_id, INVALID_PARAMS, str(e))
        except Exception as e:
            log.error("handler_error", method=method, error=str(e))
            return self._error_response(req_id, INTERNAL_ERROR, str(e))

    def _success_response(self, req_id: int | None, result: Any) -> str:
        """Build success response."""
        return json.dumps({
            "jsonrpc": "2.0",
            "result": result,
            "id": req_id,
        })

    def _error_response(self, req_id: int | None, code: int, message: str) -> str:
        """Build error response."""
        return json.dumps({
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": req_id,
        })
