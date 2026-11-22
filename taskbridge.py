"""
PLE TaskBridge — WebSocket Protocol Implementation
===================================================
Implements Version 1 of the Physical-Engineering's Last Exam (PLE)
evaluator-harness WebSocket communication protocol.
"""

import asyncio
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional
import websockets
from websockets.server import WebSocketServerProtocol


@dataclass
class ExecResult:
    """Result of a shell command executed inside the task container."""
    output: str
    exit_code: int
    truncated: bool = False
    timed_out: bool = False


class Session:
    """Represents an active engineering task evaluation session."""

    def __init__(
        self,
        ws: WebSocketServerProtocol,
        task_data: dict[str, Any],
    ):
        self.ws = ws
        self.session_id: str = task_data.get("session", "")
        self.instruction: str = task_data.get("instruction", "")
        self.workdir: str = task_data.get("workdir", "/app")
        self.limits: dict[str, Any] = task_data.get("limits", {})
        self.mcp_servers: list[dict[str, Any]] = task_data.get("mcp_servers", [])
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._is_cancelled: bool = False

    async def exec(self, command: str, timeout_sec: int = 180) -> ExecResult:
        """Execute a shell command inside the task container."""
        req_id = uuid.uuid4().hex[:16]
        fut = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = fut

        payload = {
            "type": "exec",
            "id": req_id,
            "cmd": command,
            "timeout_sec": timeout_sec,
        }
        await self.ws.send(json.dumps(payload))

        try:
            res = await asyncio.wait_for(fut, timeout=timeout_sec + 10)
            return ExecResult(
                output=res.get("output", ""),
                exit_code=res.get("exit_code", 0),
                truncated=res.get("truncated", False),
                timed_out=res.get("timed_out", False),
            )
        except asyncio.TimeoutError:
            return ExecResult(
                output=f"TaskBridge timeout awaiting response for: {command}",
                exit_code=-1,
                timed_out=True,
            )
        finally:
            self._pending_requests.pop(req_id, None)

    async def read_file(self, path: str) -> str:
        """Read a file from the task container."""
        req_id = uuid.uuid4().hex[:16]
        fut = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = fut

        payload = {
            "type": "read",
            "id": req_id,
            "path": path,
        }
        await self.ws.send(json.dumps(payload))

        try:
            res = await fut
            data = res.get("data", "")
            return data
        finally:
            self._pending_requests.pop(req_id, None)

    async def write_file(self, path: str, content: str | bytes) -> bool:
        """Write text or binary data to a file in the task container."""
        req_id = uuid.uuid4().hex[:16]
        fut = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = fut

        if isinstance(content, bytes):
            import base64
            data_str = base64.b64encode(content).decode("ascii")
            encoding = "base64"
        else:
            data_str = content
            encoding = "utf-8"

        payload = {
            "type": "write",
            "id": req_id,
            "path": path,
            "data": data_str,
            "encoding": encoding,
        }
        await self.ws.send(json.dumps(payload))

        try:
            res = await fut
            return res.get("ok", True)
        finally:
            self._pending_requests.pop(req_id, None)

    async def log(self, message: str):
        """Stream an informational log message back to the evaluator."""
        payload = {"type": "log", "message": str(message)}
        try:
            await self.ws.send(json.dumps(payload))
        except Exception:
            pass

    async def done(self):
        """Signal that the agent has finished the engineering task."""
        payload = {"type": "done"}
        await self.ws.send(json.dumps(payload))

    def handle_incoming_message(self, msg_str: str):
        """Route incoming response or cancellation frames."""
        try:
            msg = json.loads(msg_str)
        except json.JSONDecodeError:
            return

        msg_type = msg.get("type")
        if msg_type == "result":
            req_id = msg.get("id")
            if req_id and req_id in self._pending_requests:
                fut = self._pending_requests[req_id]
                if not fut.done():
                    fut.set_result(msg)
        elif msg_type == "cancel":
            self._is_cancelled = True
            print(f"[TaskBridge] Task cancelled: {msg.get('reason', 'unknown')}")


async def _run_server(solve_handler: Callable[[Session], Coroutine[Any, Any, None]]):
    port = int(os.environ.get("PORT", "8080"))
    host = "0.0.0.0"

    print(f"🚀 PLE TaskBridge Server listening on ws://{host}:{port}")

    async def handler(websocket: WebSocketServerProtocol):
        print("[TaskBridge] Evaluator connected via WebSocket.")
        session: Optional[Session] = None

        try:
            # First message from evaluator must be the "task" frame
            first_msg = await websocket.recv()
            task_data = json.loads(first_msg)

            if task_data.get("type") != "task":
                print(f"[TaskBridge] Expected 'task' message, got: {task_data.get('type')}")
                return

            session = Session(ws=websocket, task_data=task_data)
            print(f"[TaskBridge] Received Task: {session.session_id}")
            print(f"[TaskBridge] Workdir: {session.workdir}")
            print(f"[TaskBridge] Instruction snippet: {session.instruction[:150]}...")

            # Background message listener for results / cancellations
            async def listener():
                async for raw_message in websocket:
                    if session:
                        session.handle_incoming_message(raw_message)

            listener_task = asyncio.create_task(listener())

            # Run solver agent loop
            try:
                await solve_handler(session)
            finally:
                # Mark done if not already called
                try:
                    await session.done()
                except Exception:
                    pass
                listener_task.cancel()

        except websockets.exceptions.ConnectionClosed:
            print("[TaskBridge] WebSocket connection closed.")
        except Exception as e:
            print(f"[TaskBridge] Exception in handler: {e}")
            import traceback
            traceback.print_exc()

    # Serve with high message size limit (16 MiB protocol spec)
    async with websockets.serve(
        handler,
        host,
        port,
        max_size=16 * 1024 * 1024,
        ping_interval=30,
        ping_timeout=60,
    ):
        await asyncio.Future()  # run forever


def run(solve_handler: Callable[[Session], Coroutine[Any, Any, None]]):
    """Entry point to launch the harness WebSocket server."""
    try:
        asyncio.run(_run_server(solve_handler))
    except KeyboardInterrupt:
        print("\n[TaskBridge] Server stopped by user.")
