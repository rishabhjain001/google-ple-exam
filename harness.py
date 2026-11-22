"""
PLE Autonomous Engineer Agent Harness
======================================
Multi-turn agent loop for Physical-Engineering's Last Exam (PLE).
Interacts with the task environment via TaskBridge and calls frontier
Google Cloud foundation models via AsyncOpenAI.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any
from openai import AsyncOpenAI

from taskbridge import Session

# Load system instructions
PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT = (PROMPTS_DIR / "system.md").read_text(encoding="utf-8")

# Define Tool Schemas (OpenAI function calling standard)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "exec_command",
            "description": "Execute a shell command inside the task container (e.g. ls, grep, python script.py).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute in /app.",
                    },
                    "timeout_sec": {
                        "type": "integer",
                        "description": "Execution timeout in seconds (default 180).",
                        "default": 180,
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read text or data from a file inside the task container.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file in /app.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file with calculations, reports, drawings, or scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file in /app.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The exact content to write.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish_task",
            "description": "Call this tool when all engineering calculations, design files, and deliverables are complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Concise summary of completed engineering deliverables.",
                    },
                },
                "required": ["summary"],
            },
        },
    },
]


async def solve_task(session: Session, max_turns: int = 30) -> None:
    """
    Main autonomous engineering solver.
    Driven by the Google-sponsored model endpoint injected by the evaluation harness.
    """
    print(f"\n{'='*70}")
    print(f"🏗️  STARTING PLE ENGINEERING TASK: {session.session_id}")
    print(f"{'='*70}")

    await session.log(f"Starting solver for session {session.session_id}")

    # Initialize client (uses injected OPENAI_BASE_URL and OPENAI_API_KEY)
    client = AsyncOpenAI()

    # Model name from env or default
    model_name = os.environ.get("MODEL_NAME", "default")

    # Initial conversation context
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"## Physical Engineering Task\n\n"
                f"{session.instruction}\n\n"
                f"**Workspace**: `{session.workdir}`\n\n"
                f"Begin by exploring the workspace to inspect project files, drawings, "
                f"and specifications. Perform rigorous calculations with Python and generate "
                f"all required deliverables. When finished, call finish_task."
            ),
        },
    ]

    for turn in range(max_turns):
        print(f"\n--- Turn {turn + 1}/{max_turns} ---")

        try:
            # Query the Google-sponsored foundation model
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.2,
            )
        except Exception as e:
            error_msg = f"LLM completion error: {e}"
            print(f"[Harness Error]: {error_msg}")
            await session.log(error_msg)
            break

        choice = response.choices[0]
        message = choice.message
        tool_calls = message.tool_calls or []

        # Append assistant turn
        messages.append(message.model_dump(exclude_unset=True))

        if message.content:
            preview = message.content[:200].replace("\n", " ")
            print(f"[Agent Thoughts]: {preview}...")

        # If no tool calls, nudge the agent
        if not tool_calls:
            print("[Agent]: No tool called. Prompting next action.")
            messages.append({
                "role": "user",
                "content": "Please proceed by using an available tool (exec_command, read_file, write_file) or call finish_task if done.",
            })
            continue

        # Process tool calls
        task_completed = False
        for tool_call in tool_calls:
            call_id = tool_call.id
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                func_args = {}

            print(f"  🔧 Tool: {func_name}({str(func_args)[:120]})")

            result_str = ""
            if func_name == "exec_command":
                cmd = func_args.get("command", "")
                t_out = func_args.get("timeout_sec", 180)
                res = await session.exec(cmd, timeout_sec=t_out)
                result_str = f"Exit code: {res.exit_code}\nOutput:\n{res.output}"
                if res.timed_out:
                    result_str = f"Command timed out ({t_out}s)"

            elif func_name == "read_file":
                path = func_args.get("path", "")
                data = await session.read_file(path)
                result_str = data[:10000] if len(data) > 10000 else data

            elif func_name == "write_file":
                path = func_args.get("path", "")
                content = func_args.get("content", "")
                ok = await session.write_file(path, content)
                result_str = f"Wrote {len(content)} characters to {path}. Success: {ok}"

            elif func_name == "finish_task":
                summary = func_args.get("summary", "Done")
                print(f"✅ Engineering task completed! Summary: {summary}")
                await session.log(f"Deliverables finalized: {summary}")
                task_completed = True
                result_str = "Task marked complete."

            else:
                result_str = f"Unknown tool: {func_name}"

            # Truncate very large outputs to preserve context
            if len(result_str) > 8000:
                result_str = result_str[:4000] + "\n...[TRUNCATED]...\n" + result_str[-2000:]

            # Append tool result message
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": result_str,
            })

        if task_completed:
            break

        # Context management: compact if history grows too large
        if len(messages) > 35:
            print("  📦 Compacting message history...")
            messages = messages[:2] + [
                {"role": "user", "content": "[Earlier engineering steps compacted]"}
            ] + messages[-8:]

    print(f"\n🎉 Solved session: {session.session_id}")
