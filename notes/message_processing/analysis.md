# Message Processing Failure Analysis

**Date**: 2025-10-15 17:45  
**Status**: 🔴 DEBUGGING IN PROGRESS  
**Mode**: Debugging

---

## 🎯 Problem Summary

MCP server successfully connects and sends tool requests to backend, but the **future promise never gets fulfilled**. The tool request reaches the frontend via WebSocket but fails during message processing, preventing the tool executor from ever being called.

---

## 📊 Test Results

### What Works ✅
1. MCP server connects to backend successfully
2. Backend WebSocket manager routes messages correctly
3. Tool request (`query_workflow`) gets forwarded from backend → frontend
4. Frontend WebSocket receives the message
5. Tool executor initializes with all 37 tools

### What Fails ❌
1. Frontend message processing throws `MESSAGE_PROCESSING_ERROR`
2. Tool executor never gets called
3. Future promise times out after 30s
4. No response sent back to MCP server

---

## 🔍 Evidence from Logs

### Backend Log (`notes/backend.log`)

**Successful Connection:**
```
2025-10-15 17:45:01,652 - manager - INFO - New session b115cf0e-5a0d-4402-851d-8b7ee4f69e4a created with frontend connection
2025-10-15 17:45:01,652 - backend.server - INFO - Session b115cf0e-5a0d-4402-851d-8b7ee4f69e4a - frontend connected
```

**Tool Request Sent:**
```
2025-10-15 17:45:12,151 - backend.server - INFO - User message from b115cf0e-5a0d-4402-851d-8b7ee4f69e4a: what's the cfg on the ksampler?
```

**Request Forwarded to Frontend:**
```
2025-10-15 17:45:12,xxx - manager - INFO - Forwarding tool request to frontend
```

**Timeout After 30s:**
```
2025-10-15 17:45:42,xxx - ERROR - Tool execution timeout: query_workflow
```

### Frontend Log (`notes/frontend.log`)

**Tool Executor Initialized:**
```
[FL_JS] Tool executor initialized with 37 tools
[FL_JS] Registered tool: query_workflow
[FL_JS] Registered tool: workflow_overview
...
```

**WebSocket Connected:**
```
[FL_JS] WebSocket connected to backend
[FL_JS] Handshake sent to backend
```

**Message Processing Error:**
```
[FL_JS] Error: Object { 
  session_id: "b115cf0e-5a0d-4402-851d-8b7ee4f69e4a", 
  type: "error", 
  timestamp: null, 
  error_code: "MESSAGE_PROCESSING_ERROR", 
  message: "Failed to process message", 
  details: {...} 
}
```

---

## 🧩 Root Cause Hypothesis

The message flow breaks at the **frontend message handler**:

```
MCP Server (backend/mcp_server.py)
    ↓
Backend Manager (backend/manager.py)
    ↓ WebSocket
Frontend WS Client (web/extensions/FL_JS/js/ws_client.js)
    ↓ ❌ MESSAGE_PROCESSING_ERROR
Tool Executor (web/extensions/FL_JS/js/tool_executor.js) ← NEVER REACHED
```

**Likely causes:**
1. Message format mismatch between backend and frontend
2. Frontend message handler doesn't recognize tool request format
3. Missing message type routing in frontend WebSocket client
4. Tool executor not properly registered with message handler

---

## 🔧 Files to Investigate

### Backend (Sending Side)
- `backend/mcp_server.py` - MCP tool definitions and Context usage
- `backend/manager.py` - WebSocket message routing and tool request forwarding
- `backend/callback_router.py` - Future promise management

### Frontend (Receiving Side)
- `web/extensions/FL_JS/js/ws_client.js` - WebSocket message handling and parsing
- `web/extensions/FL_JS/js/tool_executor.js` - Tool execution logic
- `web/extensions/FL_JS/js/extension.js` - Extension initialization and wiring

---

## 🎯 Next Investigation Steps

1. **Check message format** sent from `backend/manager.py`
   - What does the tool request message look like?
   - Does it match what frontend expects?

2. **Trace frontend message handler** in `web/extensions/FL_JS/js/ws_client.js`
   - How does it parse incoming messages?
   - What message types does it recognize?
   - Where does it route tool requests?

3. **Verify tool executor integration** in `web/extensions/FL_JS/js/tool_executor.js`
   - Is it registered to receive messages?
   - Does it expect a specific message format?
   - How does it send responses back?

4. **Add debug logging** to see exact message content
   - Log raw message in frontend before parsing
   - Log parsed message structure
   - Log routing decision

---

## 💡 Questions to Answer

- [ ] What message format does backend send for tool requests?
- [ ] What message format does frontend expect?
- [ ] How are tool requests routed to the tool executor?
- [ ] Is there a message type field that needs to match?
- [ ] Does the tool executor need to be explicitly registered?
- [ ] Are there any middleware layers that could be failing?

---

## 📝 Related Notes

- [Tool Execution Investigation](../tool_execution/investigation.md) - Original refactoring plan
- Backend log: `notes/backend.log`
- Frontend log: `notes/frontend.log`
