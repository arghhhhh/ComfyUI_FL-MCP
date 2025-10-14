# ComfyUI Custom Nodes Research

**Date:** 2025-10-14  
**Source:** https://docs.comfy.org/custom-nodes/walkthrough  
**Purpose:** Understand ComfyUI custom node requirements for FL_JS integration

---

## Overview

ComfyUI custom nodes are extensions that can add both server-side (Python) and client-side (JavaScript) functionality. Our FL_JS system is a **Connected Client/Server** type custom node that provides:
- Backend: FastAPI WebSocket server for AI agent communication
- Frontend: Chat UI and tool execution in ComfyUI interface

---

## Required File Structure

### Standard ComfyUI Custom Node Structure
```
ComfyUI/custom_nodes/
└── YourCustomNode/
    ├── __init__.py          # REQUIRED: Exports NODE_CLASS_MAPPINGS
    ├── src/
    │   └── nodes.py          # Node class definitions
    └── web/
        └── js/                # Frontend JavaScript extensions
            └── extension.js
```

### Key Requirements

1. **Must be placed in:** `ComfyUI/custom_nodes/` directory
2. **Must have:** `__init__.py` at package root
3. **Must export:** `NODE_CLASS_MAPPINGS` dictionary
4. **Optional:** `WEB_DIRECTORY` for JavaScript extensions
5. **Optional:** `NODE_DISPLAY_NAME_MAPPINGS` for UI names

---

## __init__.py Requirements

### Minimal __init__.py
```python
# Import node classes
from .src.nodes import MyNode

# REQUIRED: Map node identifiers to classes
NODE_CLASS_MAPPINGS = {
    "MyNode": MyNode,
}

# OPTIONAL: Custom display names in UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "MyNode": "My Custom Node",
}

# REQUIRED if you have JavaScript extensions
WEB_DIRECTORY = "./web/js"

# Export for ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
```

### Key Points
- `NODE_CLASS_MAPPINGS`: Dictionary mapping string IDs to Python classes
- `WEB_DIRECTORY`: Path to JavaScript files (relative to __init__.py)
- `__all__`: Explicitly declare exports

---

## Node Class Structure

### Required Components

Every ComfyUI node class must have these 4 components:

```python
class MyNode:
    # 1. CATEGORY: Where node appears in "Add Node" menu
    CATEGORY = "example"
    
    # 2. INPUT_TYPES: Define node inputs
    @classmethod    
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "mode": (["option1", "option2"],)
            }
        }
    
    # 3. RETURN_TYPES: Define node outputs (tuple)
    RETURN_TYPES = ("IMAGE",)
    
    # 4. FUNCTION: Name of method to execute
    FUNCTION = "process"
    
    # The actual processing function
    def process(self, images, mode):
        # Process inputs
        result = images  # ... do something
        return (result,)  # Must return tuple matching RETURN_TYPES
```

### Input Types
- Standard types: `"IMAGE"`, `"STRING"`, `"INT"`, `"FLOAT"`, etc.
- Dropdown options: `["option1", "option2"]`
- Required vs optional inputs

### Return Types
- Must be a **tuple** of type strings
- Must match the return value structure

---

## Loading Mechanism

### How ComfyUI Discovers Nodes

1. **Startup Scan**: ComfyUI scans `custom_nodes/` directory at startup
2. **Import __init__.py**: Imports each package's `__init__.py`
3. **Register Nodes**: Reads `NODE_CLASS_MAPPINGS` from each package
4. **Load JavaScript**: If `WEB_DIRECTORY` is defined, loads JS files
5. **Restart Required**: Changes require ComfyUI restart

### Important Notes
- No hot-reloading (must restart ComfyUI)
- All nodes registered at startup
- JavaScript extensions loaded automatically

---

## Client-Server Communication

### Server to Client (Python to JavaScript)

```python
from server import PromptServer

# In your node's processing function
PromptServer.instance.send_sync("my.event.name", {"data": "value"})
```

### Client to Server (JavaScript to Python)

```javascript
app.registerExtension({
    name: "my.extension",
    async setup() {
        // Listen for events from server
        app.api.addEventListener("my.event.name", (event) => {
            console.log(event.detail);  // {data: "value"}
        });
    },
});
```

### Key Points
- Use `PromptServer.instance.send_sync()` for server→client
- Use `app.api.addEventListener()` for client listening
- Custom event names (use namespacing: `"mynode.event.type"`)

---

## JavaScript Extension Structure

### Basic Extension Template

```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "my.extension.name",
    
    async setup() {
        // Called once at startup
        console.log("Extension loaded");
    },
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Called for each node type before registration
    },
    
    async nodeCreated(node) {
        // Called when a node instance is created
    },
});
```

### Extension Lifecycle
- `setup()`: Called once at app startup
- `beforeRegisterNodeDef()`: Called for each node type
- `nodeCreated()`: Called for each node instance

---

## Custom Node Categories

### Types of Custom Nodes

1. **Server-side only**: Pure Python processing nodes
   - Define node class with INPUT_TYPES, RETURN_TYPES, FUNCTION
   - No JavaScript needed
   - Example: Image processing, model inference

2. **Client-side only**: Pure UI modifications
   - JavaScript extensions only
   - No Python nodes
   - Example: UI enhancements, keyboard shortcuts

3. **Independent Client/Server**: Separate features
   - Python nodes + JavaScript UI enhancements
   - No direct communication
   - Example: Node pack with UI theme

4. **Connected Client/Server**: Integrated features ⭐ **FL_JS is this type**
   - Python nodes + JavaScript extensions
   - Direct communication via PromptServer
   - Example: Real-time chat, interactive tools
   - **Note**: Won't work in API-only mode

---

## Best Practices

### File Organization
- Keep node classes in `src/nodes.py`
- Keep JavaScript in `web/js/`
- Use clear, descriptive names
- Namespace your events and extensions

### Naming Conventions
- Node IDs: CamelCase or descriptive strings
- Categories: lowercase with underscores
- Events: namespace.module.action format
- Extensions: namespace.extension format

### Dependencies
- Include `requirements.txt` for Python dependencies
- ComfyUI will prompt users to install dependencies
- Use ComfyUI's embedded Python environment

### Version Control
- Use Git for version control
- Include `.gitignore` for Python artifacts
- Tag releases for stability

---

## FL_JS Specific Considerations

### Our Architecture

FL_JS is a **Connected Client/Server** custom node:
- **Backend**: Standalone FastAPI WebSocket server (not a ComfyUI node)
- **Frontend**: JavaScript extension for chat UI
- **Communication**: WebSocket (not PromptServer)

### Key Differences

1. **No Traditional Nodes**: We don't create processing nodes
2. **Standalone Backend**: FastAPI runs separately from ComfyUI
3. **WebSocket Protocol**: Custom protocol, not PromptServer events
4. **Tool Execution**: JavaScript calls FL_JS API, sends results via WebSocket

### What We Need

1. **__init__.py**: Minimal, just for ComfyUI recognition
2. **WEB_DIRECTORY**: Point to our frontend JavaScript
3. **No NODE_CLASS_MAPPINGS**: We're not creating nodes (optional: could be empty dict)
4. **JavaScript Extension**: Our chat UI and tool executor

---

## Questions & Clarifications

### Q: Do we need NODE_CLASS_MAPPINGS if we have no nodes?
**A:** Yes, ComfyUI expects it. We can provide an empty dict `{}` or a dummy node.

### Q: Can we run a separate server?
**A:** Yes! Our FastAPI server runs independently. The JavaScript extension connects to it.

### Q: How does ComfyUI load our extension?
**A:** If `WEB_DIRECTORY` is defined, ComfyUI automatically loads all `.js` files in that directory.

### Q: Do we need to restart ComfyUI for changes?
**A:** Yes for Python changes. JavaScript changes require browser refresh (Ctrl+Shift+R).

---

## References

- **Official Docs**: https://docs.comfy.org/custom-nodes/walkthrough
- **Node Registry**: https://registry.comfy.org
- **Templates**:
  - https://github.com/Comfy-Org/cookiecutter-comfy-extension
  - https://github.com/Comfy-Org/ComfyUI-React-Extension-Template

---

**Next Steps:** Create implementation plan for integrating FL_JS with ComfyUI custom node structure.
