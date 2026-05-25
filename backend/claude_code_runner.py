"""Hidden Claude Code execution path for the Cloud provider."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from auth_service import auth_service
from config import settings


PROJECT_ROOT = Path(__file__).parent.parent
MCP_SERVER_PATH = Path(__file__).parent / "mcp_server.py"

DISALLOWED_CLAUDE_TOOLS = [
    "Task",
    "Skill",
    "EnterPlanMode",
    "ExitPlanMode",
    "TodoWrite",
    "AskUserQuestion",
    "ToolSearch",
    "ScheduleWakeup",
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    "Glob",
    "Grep",
    "NotebookRead",
    "NotebookEdit",
    "Bash",
    "BashOutput",
    "KillBash",
    "KillShell",
    "WebFetch",
    "WebSearch",
    "Monitor",
    "PushNotification",
    "RemoteTrigger",
    "TaskOutput",
    "TaskStop",
    "CronCreate",
    "CronDelete",
    "CronList",
    "EnterWorktree",
    "ExitWorktree",
]


def _mcp_config(session_id: str) -> Dict[str, Any]:
    return {
        "mcpServers": {
            "ren": {
                "command": sys.executable,
                "args": [str(MCP_SERVER_PATH)],
                "env": {
                    "FL_SESSION_ID": session_id,
                    "FL_WS_URL": f"ws://{settings.ws_host}:{settings.ws_port}/ws",
                    "FL_MCP_MODE": "subprocess",
                },
            }
        }
    }


async def run_claude_code(
    *,
    session_id: str,
    prompt: str,
    system_prompt: str,
    model: str,
    stream_handle: Any,
    block_index: int,
) -> Dict[str, int]:
    """Run Claude Code as a hidden process and publish stream deltas."""

    access_token = await auth_service.get_valid_access_token()
    env = os.environ.copy()
    env["CLAUDE_CODE_OAUTH_TOKEN"] = access_token

    config_file: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(_mcp_config(session_id), f)
            config_file = f.name

        cmd = [
            "claude",
            "-p",
            prompt,
            "--model",
            model,
            "--system-prompt",
            system_prompt,
            "--output-format",
            "stream-json",
            "--include-partial-messages",
            "--verbose",
            "--permission-mode",
            "bypassPermissions",
            "--dangerously-skip-permissions",
            "--no-session-persistence",
            "--mcp-config",
            config_file,
            "--strict-mcp-config",
            "--disallowedTools",
            ",".join(DISALLOWED_CLAUDE_TOOLS),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        full_text = ""
        input_tokens = 0
        output_tokens = 0

        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            try:
                message = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            if message.get("type") == "stream_event":
                event = message.get("event") or {}
                if event.get("type") == "message_start":
                    usage = (event.get("message") or {}).get("usage") or {}
                    input_tokens += int(usage.get("input_tokens") or 0)
                elif event.get("type") == "content_block_delta":
                    delta = event.get("delta") or {}
                    text = delta.get("text")
                    if delta.get("type") == "text_delta" and text:
                        full_text += text
                        await stream_handle.publish({
                            "type": "text_delta",
                            "blockIndex": block_index,
                            "text": text,
                        })
                elif event.get("type") == "message_delta":
                    usage = event.get("usage") or {}
                    output_tokens += int(usage.get("output_tokens") or 0)
            elif message.get("type") == "result":
                usage = message.get("usage") or {}
                input_tokens = int(usage.get("input_tokens") or input_tokens)
                output_tokens = int(usage.get("output_tokens") or output_tokens)
                result = message.get("result")
                if isinstance(result, str) and result and not full_text:
                    full_text = result
                    await stream_handle.publish({
                        "type": "text_delta",
                        "blockIndex": block_index,
                        "text": result,
                    })

        stderr = ""
        if proc.stderr is not None:
            stderr = (await proc.stderr.read()).decode("utf-8", errors="replace").strip()
        return_code = await proc.wait()
        if return_code != 0:
            raise RuntimeError(stderr or f"Claude Code exited with status {return_code}")

        return {
            "inputTokens": input_tokens,
            "outputTokens": output_tokens,
        }
    finally:
        if config_file:
            try:
                os.unlink(config_file)
            except FileNotFoundError:
                pass
