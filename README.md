# ComfyUI FL-MCP

ComfyUI FL-MCP is an MCP server and browser bridge for controlling ComfyUI from MCP-compatible clients.

It exposes ComfyUI workflow, node, queue, Manager, model, filesystem, and diagnostics tools through FastMCP. Tools that can be handled through ComfyUI's HTTP API work in standalone mode. Tools that need live canvas state use the optional browser bridge loaded as a ComfyUI custom node.

## Features

- MCP tools for workflow inspection, node queries, queue control, Manager v4, model/resource discovery, and ComfyUI diagnostics.
- Optional ComfyUI browser bridge for canvas-only operations such as reading the current graph, selecting/focusing nodes, layout edits, screenshots, and frontend commands.
- Embedded custom-node mode with a small FL-MCP status panel.
- Standalone MCP mode for REST-only ComfyUI control.
- Safety gates for write/destructive operations.

## Install

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/filliptm/ComfyUI_FL-MCP.git
cd ComfyUI_FL-MCP
pip install -r requirements.txt
```

Restart ComfyUI after installation. The ComfyUI sidebar will show an `FL-MCP` bridge status tab.

## Embedded Bridge Mode

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

Start ComfyUI normally. If `AUTO_START_BACKEND=true`, the bridge backend starts with ComfyUI. Otherwise, use the FL-MCP sidebar button or start it manually:

```bash
cd /path/to/ComfyUI/custom_nodes/ComfyUI_FL-MCP/backend
python server.py
```

Bridge server endpoints:

- `GET /health`
- `GET /api/config`
- `GET /api/mcp/status`
- `POST /api/mcp/shutdown`
- `GET /api/sessions`
- `WS /ws`
- `GET /api/comfy/status`
- `GET /api/comfy/logs`

## Standalone MCP Mode

For REST-only tools:

```bash
cd /path/to/ComfyUI/custom_nodes/ComfyUI_FL-MCP
python backend/mcp_server.py
```

Set `COMFYUI_SERVER_URL` if ComfyUI is not on `http://127.0.0.1:8188`.

Browser-only tools require the bridge server and a browser session. Run the MCP server with:

```bash
FL_MCP_MODE=subprocess
FL_MCP_SESSION_ID=<session-id-from-sidebar>
FL_MCP_WS_URL=ws://127.0.0.1:8000/ws
python backend/mcp_server.py
```

If a browser-only tool is called without the bridge, it returns a `requires_browser_bridge` error.

## Safety Gates

Read-only tools are enabled by default. Mutating tools require explicit opt-in:

```bash
FL_MCP_ENABLE_WORKFLOW_WRITES=false
FL_MCP_ENABLE_CUSTOM_NODE_WRITES=false
FL_MCP_ENABLE_GIT_WRITES=false
FL_MCP_ENABLE_MANAGER_MUTATIONS=false
FL_MCP_ENABLE_COMFY_PROCESS_CONTROL=false
```

Set only the permissions you need to `true`.

## Tool Categories

- `workflow_*`: current graph, saved workflow files, tabs, load/save operations.
- `find_node`, `get_node_values`, `get_node_slots`, `connect_nodes*`: node inspection and graph operations.
- `queue_*` and `comfy_*`: queue, history, settings, models, assets, tags, logs, process status.
- `manager_*`: ComfyUI Manager v4 status, queue, installed packs, mappings, external models.
- `node_library_*`: node definition search and compatibility lookup.
- `custom_nodes_*`: scoped inspection and optional write/git operations under `custom_nodes`.
- `mcp_capability_audit`: current bridge, REST, Manager, assets, and safety-gate status.

## Development

```bash
pytest
```

The default test config includes coverage. Install `requirements.txt` before running tests.
