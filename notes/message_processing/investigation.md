# Message Processing Investigation

**Date**: 2025-10-15  
**Status**: 🔍 INVESTIGATING  
**Reference**: [Implementation Summary](../tool_execution/implementation_summary.md)

---

## 📚 Context from Implementation

According to `notes/tool_execution/implementation_summary.md`, the expected message flow is:

### Expected Flow (Step 7-10)
```
7. MCP subprocess → WebSocket → Backend (tool_request)
   ↓
8. Backend → route_tool_request_to_frontend()
   ↓
9. Backend → WebSocket → Frontend (tool_request)
   ↓
10. Frontend → ToolExecutor.executeToolRequest()
```

### Expected Message Types
From implementation summary:
1. **handshake**: Initial connection setup
2. **handshake_ack**: Acknowledgment from server
3. **user_message**: User chat message
4. **agent_response**: Agent response to user
5. **tool_request**: Tool execution request (MCP → Frontend) ⭐
6. **tool_result**: Tool execution result (Frontend → MCP)
7. **error**: Error message

### Expected Tool Request Format
Based on implementation, should contain:
- `type`: `"tool_request"`
- `request_id`: UUID for pairing
- `tool_name`: Name of tool to execute
- `parameters`: Tool parameters
- `session_id`: Session identifier

---

## ❓ Investigation Questions

### 1. Backend Message Format
**File**: `backend/server.py` - `route_tool_request_to_frontend()`

- [ ] What exact format does backend send?
- [ ] Does it include all required fields?
- [ ] Is the `type` field set to `"tool_request"`?
- [ ] Are parameters properly serialized?

### 2. Frontend Message Handler
**File**: `web/extensions/FL_JS/js/ws_client.js`

- [ ] What message types does it recognize?
- [ ] How does it parse incoming messages?
- [ ] Where does it route `tool_request` messages?
- [ ] Does it validate message structure?

### 3. Tool Executor Integration
**File**: `web/extensions/FL_JS/js/tool_executor.js`

- [ ] Is `executeToolRequest()` method present?
- [ ] How is it called from ws_client?
- [ ] What format does it expect?
- [ ] How does it send back `tool_result`?

---

## 🔍 Investigation Plan

### Step 1: Check Backend Message Sending

**File to examine**: `backend/server.py`

Look for:
```python
async def route_tool_request_to_frontend(session_id: str, data: dict):
    # What does this function send?
    # Format of message?
```

**Expected behavior** (from implementation summary):
- Should forward `tool_request` to frontend connection
- Should include `request_id`, `tool_name`, `parameters`

### Step 2: Trace Frontend Message Reception

**File to examine**: `web/extensions/FL_JS/js/ws_client.js`

Look for:
```javascript
// WebSocket message handler
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    // How is message.type handled?
    // Where does 'tool_request' route to?
}
```

**Expected behavior**:
- Parse JSON message
- Check `type` field
- Route `tool_request` to ToolExecutor

### Step 3: Verify Tool Executor Method

**File to examine**: `web/extensions/FL_JS/js/tool_executor.js`

Look for:
```javascript
class ToolExecutor {
    executeToolRequest(message) {
        // Does this method exist?
        // What does it expect?
    }
}
```

**Expected behavior**:
- Extract `tool_name` and `parameters`
- Execute tool via FL_API
- Send back `tool_result` via WebSocket

### Step 4: Check Message Type Routing

**Hypothesis**: Frontend might not have a case for `tool_request` type

Look for message type switch/if-else:
```javascript
switch(message.type) {
    case 'handshake_ack': ...
    case 'agent_response': ...
    case 'tool_request': ... // ← Is this missing?
    case 'error': ...
}
```

---

## 🔧 Files to Investigate (Priority Order)

1. **`backend/server.py`** (lines ~200-300)
   - Find `route_tool_request_to_frontend()`
   - Check message format sent to frontend

2. **`web/extensions/FL_JS/js/ws_client.js`** (full file)
   - Find WebSocket `onmessage` handler
   - Check message type routing
   - Verify `tool_request` case exists

3. **`web/extensions/FL_JS/js/tool_executor.js`** (full file)
   - Find `executeToolRequest()` method
   - Check if it's properly integrated
   - Verify response sending logic

4. **`web/extensions/FL_JS/js/extension.js`** (initialization)
   - Check how ws_client and tool_executor are wired together
   - Verify tool_executor is passed to ws_client

---

## 💡 Likely Root Causes

### Hypothesis 1: Missing Message Type Handler
**Probability**: 🔴 HIGH

Frontend ws_client doesn't have a case for `tool_request` message type, causing it to fall through to error handling.

**Evidence needed**:
- Check ws_client.js message type switch
- Look for `case 'tool_request':`

### Hypothesis 2: Wrong Message Format
**Probability**: 🟡 MEDIUM

Backend sends message in different format than frontend expects.

**Evidence needed**:
- Compare backend send format
- Compare frontend expected format

### Hypothesis 3: Tool Executor Not Connected
**Probability**: 🟡 MEDIUM

Tool executor instance not passed to ws_client, so routing fails.

**Evidence needed**:
- Check extension.js initialization
- Verify tool_executor reference in ws_client

### Hypothesis 4: Message Validation Failure
**Probability**: 🟢 LOW

Frontend validates message structure and rejects it before routing.

**Evidence needed**:
- Check for validation logic in ws_client
- Look for required field checks

---

## 📝 Next Actions

1. **Read `backend/server.py`** - Find `route_tool_request_to_frontend()`
2. **Read `web/extensions/FL_JS/js/ws_client.js`** - Find message handler
3. **Compare formats** - Document any mismatches
4. **Identify fix** - Determine what needs to change
5. **Update analysis.md** - Document findings

---

## 🔗 Related Files

- Implementation summary: `notes/tool_execution/implementation_summary.md`
- Problem analysis: `notes/message_processing/analysis.md`
- Backend logs: `notes/backend.log`
- Frontend logs: `notes/frontend.log`
- Backend server: `backend/server.py`
- Backend manager: `backend/manager.py`
- MCP server: `backend/mcp_server.py`
- Frontend WS client: `web/extensions/FL_JS/js/ws_client.js`
- Frontend tool executor: `web/extensions/FL_JS/js/tool_executor.js`
- Frontend extension: `web/extensions/FL_JS/js/extension.js`
