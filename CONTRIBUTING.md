# Contributing to ComfyUI FL-MCP

Keep the project focused on being a reliable MCP server and ComfyUI bridge.

## Guidelines

- Prefer deterministic tool behavior over product-specific assistant behavior.
- Keep tools scoped and explicit about whether they are read-only or mutating.
- Guard file, git, Manager, workflow, and process mutations behind config flags.
- Avoid adding persona, conversation, or hosted-assistant features to this repo.
- Add tests for new tool schemas, routing behavior, and safety gates.
