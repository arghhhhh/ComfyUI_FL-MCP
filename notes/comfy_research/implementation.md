# FL_JS ComfyUI Integration Implementation Plan

**Date:** 2025-10-14  
**Status:** Research Complete, Ready for Implementation  
**Goal:** Adapt FL_JS codebase to conform to ComfyUI custom node structure

---

## Current State Analysis

### What We Have
```
fl_js/
├── backend/
│   ├── __init__.py       ✅ EXISTS (but wrong location)
│   ├── config.py         ✅
│   ├── models.py         ✅
│   ├── websocket.py      ✅
│   └── server.py         ✅
├── frontend/
│   ├── session_manager.js  ✅
│   └── ws_client.js        ✅
├── requirements.txt      ✅
├── .env.example          ✅
└── README.md             ✅
```

### What ComfyUI Expects
```
ComfyUI/custom_nodes/FL_JS/
├── __init__.py           ❌ MISSING (at root)
├── backend/              ✅ OK (our server code)
├── web/                  ❌ WRONG NAME (should be 'web', not 'frontend')
│   └── js/               ❌ MISSING (needs js subdirectory)
│       ├── extension.js  ❌ MISSING (main entry point)
│       ├── session_manager.js  ✅ (needs to be moved)
│       └── ws_client.js        ✅ (needs to be moved)
├── requirements.txt      ✅ OK
└── README.md             ✅ OK
```

---

## Gap Analysis

### Missing Components

1. **Root `__init__.py`** ❌
   - **Required by:** ComfyUI node loading system
   - **Purpose:** Export NODE_CLASS_MAPPINGS and WEB_DIRECTORY
   - **Action:** Create at project root

2. **Proper `web/js/` directory structure** ❌
   - **Current:** `frontend/` (flat)
   - **Required:** `web/js/` (nested)
   - **Action:** Rename and restructure

3. **Main extension entry point** ❌
   - **Missing:** `web/js/extension.js`
   - **Purpose:** Register ComfyUI extension, initialize chat UI
   - **Action:** Create extension.js that loads our modules

4. **NODE_CLASS_MAPPINGS** ❌
   - **Status:** Not defined anywhere
   - **Options:** 
     - Empty dict `{}` (we have no nodes)
     - Dummy node (for compatibility)
   - **Action:** Decide approach

---

## Implementation Strategy

### Option A: Extension-Only (Recommended) ✅

**Approach:** FL_JS is purely a JavaScript extension with external backend.

**Pros:**
- Clean separation of concerns
- Backend runs independently
- No dummy nodes needed
- Matches our architecture

**Cons:**
- Empty NODE_CLASS_MAPPINGS might confuse users
- Not discoverable in node menu

**Structure:**
```
FL_JS/
├── __init__.py                  # Exports empty mappings + WEB_DIRECTORY
├── backend/                     # Standalone FastAPI server
├── web/
│   └── js/
│       ├── extension.js         # Main entry, registers extension
│       ├── session_manager.js   # Session management
│       ├── ws_client.js         # WebSocket client
│       ├── chat_ui.js           # (Phase 4)
│       └── tool_executor.js     # (Phase 2)
├── requirements.txt
└── README.md
```

### Option B: Dummy Node (Alternative)

**Approach:** Create a dummy "FL_JS Control" node for visibility.

**Pros:**
- Discoverable in node menu
- Users can see it's installed
- Can show status/info

**Cons:**
- Node doesn't actually do anything
- Adds complexity
- Misleading (not a processing node)

**Not recommended** for our use case.

---

## Recommended Changes

### 1. Create Root `__init__.py`

**File:** `__init__.py` (at project root)

```python
"""FL_JS Agentic System for ComfyUI

AI-powered workflow assistant with natural language interface.

This is a JavaScript extension that provides a chat interface
for interacting with ComfyUI workflows via an AI agent.

Backend server must be started separately:
    cd backend
    python server.py
"""

# No nodes to register (extension-only)
NODE_CLASS_MAPPINGS = {}

# Optional: Empty display names
NODE_DISPLAY_NAME_MAPPINGS = {}

# Point to JavaScript extensions
WEB_DIRECTORY = "./web/js"

# Export for ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
```

### 2. Restructure Frontend Directory

**Action:** Rename `frontend/` to `web/js/`

```bash
# Current structure
frontend/
├── session_manager.js
└── ws_client.js

# New structure
web/
└── js/
    ├── extension.js          # NEW: Main entry point
    ├── session_manager.js    # MOVED
    ├── ws_client.js          # MOVED
    ├── chat_ui.js            # (Phase 4)
    ├── tool_executor.js      # (Phase 2)
    ├── fl_api.js             # (Phase 2)
    ├── query_executor.js     # (Phase 3)
    └── diagram_generator.js  # (Phase 4)
```

### 3. Create Main Extension Entry Point

**File:** `web/js/extension.js`

```javascript
/**
 * FL_JS Agentic System - ComfyUI Extension
 * 
 * Provides AI-powered workflow assistance via natural language chat interface.
 * Requires FL_JS backend server to be running.
 */

import { app } from "../../scripts/app.js";

// Import our modules
import SessionManager from "./session_manager.js";
import WSClient from "./ws_client.js";

app.registerExtension({
    name: "fl_js.agentic_system",
    
    async setup() {
        console.log("[FL_JS] Initializing Agentic System extension...");
        
        // Initialize session manager
        const sessionManager = new SessionManager();
        const sessionId = sessionManager.getSessionId();
        
        console.log(`[FL_JS] Session ID: ${sessionId}`);
        
        // Initialize WebSocket client
        const wsClient = new WSClient(sessionId, {
            url: 'ws://localhost:8000/ws',  // TODO: Make configurable
        });
        
        // Set up event handlers
        wsClient.onConnect = () => {
            console.log("[FL_JS] Connected to backend");
        };
        
        wsClient.onDisconnect = () => {
            console.log("[FL_JS] Disconnected from backend");
        };
        
        wsClient.onError = (error) => {
            console.error("[FL_JS] WebSocket error:", error);
        };
        
        // Store instances globally for other modules
        window.FL_JS = {
            sessionManager,
            wsClient,
            app,
        };
        
        // Connect to backend
        wsClient.connect();
        
        console.log("[FL_JS] Extension initialized");
    },
});
```

### 4. Update Module Exports

**Files:** `session_manager.js`, `ws_client.js`

```javascript
// Change from CommonJS to ES6 modules

// OLD (remove):
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionManager;
}

// NEW (add):
export default SessionManager;
```

### 5. Update README.md Installation Instructions

**Section:** Installation

```markdown
## Installation

### As ComfyUI Custom Node

1. **Clone into custom_nodes:**
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/yourusername/fl_js.git FL_JS
   cd FL_JS
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your LLM API key
   ```

4. **Start backend server:**
   ```bash
   cd backend
   python server.py
   ```

5. **Restart ComfyUI**
   - The extension will load automatically
   - Look for "[FL_JS] Initializing..." in browser console

6. **Access chat interface:**
   - Click the FL_JS tab in the sidebar
   - Start chatting with your AI assistant!
```

---

## Implementation Checklist

### Phase 1.5: ComfyUI Integration (New Phase)

- [ ] Create root `__init__.py` with NODE_CLASS_MAPPINGS and WEB_DIRECTORY
- [ ] Rename `frontend/` to `web/js/`
- [ ] Move `session_manager.js` to `web/js/`
- [ ] Move `ws_client.js` to `web/js/`
- [ ] Update module exports to ES6 (export default)
- [ ] Create `web/js/extension.js` as main entry point
- [ ] Update README.md with ComfyUI installation instructions
- [ ] Test in ComfyUI:
  - [ ] Extension loads without errors
  - [ ] WebSocket connects to backend
  - [ ] Session management works
  - [ ] Console logs show proper initialization

---

## File Changes Summary

### New Files
1. `__init__.py` (root) - ComfyUI node registration
2. `web/js/extension.js` - Main extension entry point

### Moved Files
1. `frontend/session_manager.js` → `web/js/session_manager.js`
2. `frontend/ws_client.js` → `web/js/ws_client.js`

### Modified Files
1. `web/js/session_manager.js` - Change to ES6 export
2. `web/js/ws_client.js` - Change to ES6 export
3. `README.md` - Update installation instructions

### Deleted Directories
1. `frontend/` (replaced by `web/js/`)

---

## Testing Strategy

### Test 1: Extension Loading
**Goal:** Verify ComfyUI recognizes and loads the extension

**Steps:**
1. Copy FL_JS to `ComfyUI/custom_nodes/`
2. Start ComfyUI
3. Open browser console
4. Look for: `[FL_JS] Initializing Agentic System extension...`

**Expected:** No errors, initialization message appears

### Test 2: Backend Connection
**Goal:** Verify WebSocket connects to backend

**Steps:**
1. Start backend server: `cd backend && python server.py`
2. Refresh ComfyUI
3. Check console for: `[FL_JS] Connected to backend`
4. Check backend logs for: `Session {id} connected`

**Expected:** Handshake completes, session registered

### Test 3: Session Persistence
**Goal:** Verify session persists across refreshes

**Steps:**
1. Note session ID from console
2. Refresh page
3. Check if same session ID is used
4. Backend should show "reconnected"

**Expected:** Same session ID, reconnection status

### Test 4: Multi-Window
**Goal:** Verify multiple windows work independently

**Steps:**
1. Open ComfyUI in two browser windows
2. Check console in both windows
3. Verify different session IDs
4. Backend should show 2 active sessions

**Expected:** Independent sessions, no message mixing

---

## Migration Notes

### For Existing Development
If you've already started development:

1. **Backup current work:**
   ```bash
   git commit -am "Backup before restructure"
   ```

2. **Create new branch:**
   ```bash
   git checkout -b comfyui-integration
   ```

3. **Apply changes:**
   - Follow implementation checklist
   - Test thoroughly
   - Merge back to main

### For Fresh Start
If starting fresh:

1. Apply all changes from checklist
2. Test each component
3. Proceed to Phase 2

---

## Next Steps After Integration

Once ComfyUI integration is complete:

1. **Phase 1 Complete** ✅
   - Backend foundation
   - Frontend foundation
   - ComfyUI integration

2. **Move to Phase 2: Tool System**
   - Implement `backend/callback_router.py`
   - Implement `backend/mcp_server.py`
   - Implement `web/js/fl_api.js`
   - Implement `web/js/tool_executor.js`

3. **Phase 4: Chat UI**
   - Implement `web/js/chat_ui.js`
   - Register sidebar tab
   - Full end-to-end testing

---

## Questions & Decisions

### Q: Should we create a dummy node for discoverability?
**Decision:** No. Extension-only approach is cleaner and matches our architecture.

### Q: How to handle backend server not running?
**Decision:** Extension should handle gracefully, show error in chat UI (Phase 4).

### Q: Should backend server auto-start?
**Decision:** No. Keep separate for flexibility. Document clearly in README.

### Q: Configuration for WebSocket URL?
**Decision:** Hardcode for now, make configurable in Phase 5 (Polish).

---

**Status:** Ready to implement! Let's restructure the codebase. 🚀
