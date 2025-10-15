# Message Processing Investigation - FINDINGS

**Date**: 2025-10-15  
**Status**: ✅ ROOT CAUSE IDENTIFIED - MCP SUBPROCESS NOT STARTING

---

## 🎯 ACTUAL ROOT CAUSE FOUND

**The MCP subprocess is being spawned but NOT calling `mcp.run()` to start the server!**

### The Problem

Looking at `backend/mcp_server.py` (lines 664-669):

```python
def main():
    """Run the MCP server as a standalone application."""
    mcp.run()
    
if __name__ == "__main__":
    main()
```

**This only runs when executed as `__main__`**, but when PydanticAI spawns it as a subprocess via `MCPServerStdio`, it's NOT running as `__main__`!

---

## 🔍 How PydanticAI Spawns MCP Subprocess

**File**: `backend/agent.py` (lines 229-234)

```python
mcp_servers = [
    MCPServerStdio(
        'python',
        ['backend/mcp_server.py'],
        env=mcp_env  # Pass environment to subprocess
    )
]
```

This runs: `python backend/mcp_server.py` with environment variables.

BUT... when PydanticAI's `MCPServerStdio` runs this, it expects the MCP server to:
1. Start via `mcp.run()` 
2. Connect to stdio (stdin/stdout) for MCP protocol communication
3. NOT try to connect via WebSocket

---

## 💡 The Architecture Mismatch

### What We Implemented (WebSocket-based)

```
Agent (backend/agent.py)
  ↓ spawns subprocess
MCP Server (backend/mcp_server.py)
  ↓ connects via WebSocket
Backend Server (backend/server.py)
  ↓ routes to
Frontend (web/js/tool_executor.js)
```

### What PydanticAI Expects (stdio-based)

```
Agent (backend/agent.py)
  ↓ spawns subprocess with MCPServerStdio
MCP Server (backend/mcp_server.py)
  ↓ communicates via stdin/stdout using MCP protocol
Agent (backend/agent.py)
  ↓ executes tools directly
Frontend (web/js/tool_executor.js)
```

---

## 🧩 Why The Subprocess Isn't Connecting

**The MCP subprocess needs to:**

1. ✅ Be spawned by PydanticAI (happening)
2. ✅ Have environment variables set (happening)
3. ❌ **Call `mcp.run()` to start the MCP server** (NOT happening!)
4. ❌ Connect to backend WebSocket from lifespan (can't happen until #3)

**The issue**: `mcp.run()` is only called when `__name__ == "__main__"`, but when PydanticAI spawns it, `__name__` is probably NOT `"__main__"`.

---

## 🔧 The Fix

### Option 1: Force `mcp.run()` to Always Execute

**Change `backend/mcp_server.py` line 664-669:**

```python
# OLD:
def main():
    """Run the MCP server as a standalone application."""
    mcp.run()
    
if __name__ == "__main__":
    main()

# NEW:
def main():
    """Run the MCP server as a standalone application."""
    mcp.run()

# Always run when module is loaded
main()
```

### Option 2: Check PydanticAI's MCPServerStdio Behavior

Maybe `MCPServerStdio` expects the script to auto-start the MCP server when imported. Let's verify this is the issue first.

---

## 📊 Evidence Trail

### ✅ What's Working

1. **Frontend connects successfully**
   ```
   2025-10-15 17:45:01,652 - INFO - Session xxx - frontend connected
   ```

2. **Agent spawns correctly**
   ```python
   # backend/agent.py line 227
   logger.info(f"MCP subprocess environment: session_id={session_id}...")
   ```

3. **Environment variables set**
   ```python
   mcp_env = {
       'FL_SESSION_ID': session_id,
       'FL_WS_URL': f'ws://{settings.ws_host}:{settings.ws_port}/ws',
       'FL_MCP_MODE': 'subprocess',
   }
   ```

4. **MCP lifespan manager ready**
   ```python
   # backend/mcp_server.py line 160
   @asynccontextmanager
   async def mcp_lifespan(server: FastMCP) -> AsyncIterator[Any]:
       # Checks for FL_MCP_MODE and creates WebSocket client
   ```

### ❌ What's NOT Working

1. **No MCP connection log in backend**
   - Expected: `Session xxx - mcp connected`
   - Actual: MISSING

2. **No MCP subprocess startup logs**
   - Expected: `[MCP] Starting in subprocess mode for session: xxx`
   - Expected: `[MCP-WS] Connecting to ws://...`
   - Actual: MISSING

3. **Tool request has nowhere to go**
   - Agent tries to call tool
   - No MCP subprocess to handle it
   - Times out after 30s

---

## 🔎 Diagnostic Questions

### Q1: Is the subprocess even starting?
**How to check**: Add logging at the TOP of `backend/mcp_server.py` before any async code:

```python
import sys
print("[MCP-DEBUG] Module loading, __name__ =", __name__, file=sys.stderr)
print("[MCP-DEBUG] FL_MCP_MODE =", os.getenv('FL_MCP_MODE'), file=sys.stderr)
```

### Q2: What does PydanticAI's MCPServerStdio expect?
**How to check**: Look at PydanticAI documentation or source code for `MCPServerStdio`.

Does it expect:
- A) Script to call `mcp.run()` automatically when loaded?
- B) Script to only define `if __name__ == "__main__": mcp.run()`?

### Q3: Is `mcp.run()` being called at all?
**How to check**: Add logging inside `main()`:

```python
def main():
    print("[MCP-DEBUG] main() called!", file=sys.stderr)
    mcp.run()
```

---

## 📝 Next Steps

### Step 1: Add Debug Logging
Add print statements to `backend/mcp_server.py` to see:
- Is module loading?
- What is `__name__`?
- Is `main()` being called?
- Are environment variables set?

### Step 2: Test The Fix
Try changing `backend/mcp_server.py` to always call `main()`:

```python
def main():
    """Run the MCP server as a standalone application."""
    mcp.run()

# Always run (not just when __name__ == "__main__")
main()
```

### Step 3: Verify MCP Subprocess Connects
Look for these logs after fix:
```
[MCP] Starting in subprocess mode for session: xxx
[MCP-WS] Connecting to ws://localhost:8000/ws with session xxx
[MCP-WS] Connected and handshake complete
```

And in backend:
```
Session xxx - mcp connected
```

### Step 4: Test Tool Execution
Send a user message that requires a tool call and verify:
```
[MCP-WS] Executing tool: query_workflow (request_id: xxx)
[ToolExecutor] Executing: query_workflow (request_id: xxx)
[ToolExecutor] Success: query_workflow (123.45ms)
[MCP-WS] Tool execution complete: xxx
```

---

## 📁 Files Referenced

- `backend/mcp_server.py` - MCP server with WebSocket client (lines 664-669 need fix)
- `backend/agent.py` - Agent and MCP subprocess creation (lines 229-234)
- `backend/server.py` - WebSocket message routing (working correctly)
- `web/js/ws_client.js` - Frontend WebSocket client (working correctly)
- `web/js/tool_executor.js` - Frontend tool execution (working correctly)
- `web/js/extension.js` - Extension initialization (working correctly)

---

## 🔗 Related Notes

- [Investigation Plan](investigation.md)
- [Problem Analysis](analysis.md)
- [Implementation Summary](../tool_execution/implementation_summary.md)
- Backend logs: `notes/backend.log`
- Frontend logs: `notes/frontend.log`

---

## ✅ Summary

**Root Cause**: `backend/mcp_server.py` only calls `mcp.run()` when `__name__ == "__main__"`, but PydanticAI's `MCPServerStdio` subprocess doesn't trigger this condition.

**Fix**: Change the module to always call `main()` when loaded, not just when run as main script.

**Expected Result**: MCP subprocess will start, connect to backend WebSocket, and handle tool execution requests from the agent.
