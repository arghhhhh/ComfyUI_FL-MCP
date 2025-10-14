"""FL_JS Agentic System for ComfyUI

AI-powered workflow assistant with natural language interface.

This is a JavaScript extension that provides a chat interface
for interacting with ComfyUI workflows via an AI agent.

Backend server must be started separately:
    cd backend
    python server.py

For more information, see README.md
"""

# ComfyUI Custom Node Registration
# FL_JS is an extension-only custom node (no processing nodes)

# No nodes to register (extension-only)
NODE_CLASS_MAPPINGS = {}

# Optional: Empty display names
NODE_DISPLAY_NAME_MAPPINGS = {}

# Point to JavaScript extensions
WEB_DIRECTORY = "./web/js"

# Export for ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
