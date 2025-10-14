# FL_JS Agentic System 🤖

> **AI-Powered ComfyUI Workflow Assistant** - Create, modify, and understand ComfyUI workflows through natural language conversation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Extension-orange.svg)](https://github.com/comfyanonymous/ComfyUI)

---

## ✨ Features

### 🎯 Natural Language Workflow Control
- **Chat with your workflow** - "Create a txt2img workflow with SDXL"
- **Modify on the fly** - "Change all KSampler steps to 30"
- **Query your graph** - "Show me all nodes connected to the checkpoint loader"
- **Visual feedback** - Get Mermaid diagrams of your workflow structure

### 🛠️ Comprehensive Tool Suite (40+ Tools)
- **Node Management** - Create, find, remove, bypass, pin, and select nodes
- **Node Manipulation** - Get/set parameters, connect nodes intelligently
- **Layout Control** - Auto-arrange workflows, position nodes relative to each other
- **Workflow Execution** - Queue, cancel, batch processing, monitor status
- **Advanced Queries** - Filter nodes, traverse connections, aggregate data

### 🧠 Intelligent Agent
- **Context-aware** - Remembers conversation history and workflow state
- **Proactive suggestions** - Warns about disconnected nodes, suggests improvements
- **Best practices** - Knows ComfyUI patterns and common workflow structures
- **Multi-LLM support** - Works with OpenAI, Anthropic Claude, or Google Gemini

### 🎨 Native ComfyUI Integration
- **Sidebar panel** - Seamlessly integrated into ComfyUI's left drawer
- **Dark theme** - Matches ComfyUI's aesthetic perfectly
- **Real-time updates** - WebSocket-based instant communication
- **Multi-session** - Each browser tab gets its own isolated agent

---

## 🚀 Quick Start

### Prerequisites
- **ComfyUI** installed and working
- **Python 3.11+** for the backend server
- **API Key** for your chosen LLM provider (OpenAI, Anthropic, or Google)

### Installation

#### 1. Clone into ComfyUI custom nodes
```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/yourusername/fl_js.git
cd fl_js
```

#### 2. Set up the backend
```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings
```

#### 3. Configure your LLM provider

Edit `backend/.env`:

```bash
# Choose your provider: openai, anthropic, or gemini
LLM_PROVIDER=openai

# Add your API key
OPENAI_API_KEY=sk-your-key-here
# Or for Anthropic:
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# Or for Google:
# GOOGLE_API_KEY=your-key-here

# Choose your model
LLM_MODEL=gpt-4-turbo-preview
# Or: claude-3-opus-20240229, gemini-pro, etc.
```

#### 4. Start the backend server
```bash
cd backend
uvicorn server:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### 5. Start ComfyUI
```bash
cd /path/to/ComfyUI
python main.py
```

#### 6. Open ComfyUI in your browser

Look for the **FL_JS Assistant** button (💬) in the left sidebar!

---

## 💬 Usage Examples

### Creating Workflows
```
You: "Create a simple text-to-image workflow"

Agent: "I'll create a basic txt2img workflow for you."
       [Creates and connects: CheckpointLoader → CLIPTextEncode (positive/negative) 
        → EmptyLatentImage → KSampler → VAEDecode → SaveImage]
       "Done! I've created a complete workflow with 7 nodes."
```

### Modifying Workflows
```
You: "Change the sampler to use 40 steps with euler_ancestral"

Agent: "I'll update the KSampler settings."
       [Finds KSampler node, sets steps=40, sampler_name="euler_ancestral"]
       "Updated! The sampler now uses 40 steps with euler_ancestral."
```

### Querying Workflows
```
You: "Show me all LoRA nodes and their weights"

Agent: [Queries workflow, finds LoRA loaders]
       "Found 2 LoRA nodes:
        - Node #5: 'detail_enhancer.safetensors' (weight: 0.8)
        - Node #12: 'style_helper.safetensors' (weight: 0.6)"
```

### Visual Diagrams
```
You: "Show me the workflow structure"

Agent: [Generates Mermaid diagram]
       ```mermaid
       graph LR
         N1[CheckpointLoader] --> N2[CLIPTextEncode]
         N1 --> N3[KSampler]
         N2 --> N3
         ...
       ```
```

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     ComfyUI Browser                         │
│  ┌────────────────┐              ┌────────────────────┐    │
│  │  Chat Sidebar  │◄─────────────┤   FL_JS Legacy     │    │
│  │  (extension.js)│  Tool Calls  │   (fl_js.js)       │    │
│  └────────┬───────┘              └────────────────────┘    │
│           │ WebSocket                                       │
└───────────┼─────────────────────────────────────────────────┘
            │
            │ ws://localhost:8000/ws
            │
┌───────────▼─────────────────────────────────────────────────┐
│                    Backend Server (Python)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  WebSocket   │  │  PydanticAI  │  │   FastMCP       │  │
│  │  Manager     │──┤    Agent     │──┤   Tools (40+)   │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│         │                  │                    │           │
│         └──────────────────┴────────────────────┘           │
│                     Session Management                      │
│              (Isolated per browser tab)                     │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### Frontend (JavaScript)
- **`extension.js`** - ComfyUI extension entry point, sidebar registration
- **`chat_ui.js`** - Chat interface with markdown/mermaid rendering
- **`ws_client.js`** - WebSocket client with auto-reconnection
- **`tool_executor.js`** - Executes tool callbacks from agent
- **`fl_api.js`** - Wrapper around legacy FL_JS functions
- **`query_executor.js`** - JSON-based query DSL execution
- **`diagram_generator.js`** - Mermaid diagram generation

#### Backend (Python)
- **`server.py`** - FastAPI application with WebSocket endpoint
- **`websocket.py`** - Connection manager, session routing
- **`agent.py`** - PydanticAI agent factory and management
- **`mcp_server.py`** - FastMCP tool definitions (40+ tools)
- **`callback_router.py`** - Tool callback request/response handling
- **`models.py`** - Pydantic models for messages and queries
- **`config.py`** - Configuration and settings

---

## 🔧 Configuration

### Environment Variables

All configuration is in `backend/.env`:

```bash
# === LLM Provider ===
LLM_PROVIDER=openai              # openai, anthropic, or gemini
LLM_MODEL=gpt-4-turbo-preview    # Model name
LLM_TEMPERATURE=0.7              # Creativity (0.0-1.0)
LLM_MAX_TOKENS=4000              # Max response length

# === API Keys ===
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# === WebSocket Settings ===
WS_HOST=0.0.0.0                  # Server host
WS_PORT=8000                     # Server port
WS_HEARTBEAT_INTERVAL=30         # Seconds between heartbeats
WS_SESSION_TIMEOUT=300           # Session timeout (seconds)
WS_MAX_RECONNECT_ATTEMPTS=5      # Max reconnection attempts

# === Tool Execution ===
TOOL_TIMEOUT=30000               # Tool timeout (milliseconds)
MAX_TOOL_RETRIES=3               # Max retries on tool failure

# === Conversation ===
CONVERSATION_MAX_HISTORY=50      # Max messages to remember

# === Logging ===
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                  # json or text
```

### Supported LLM Models

#### OpenAI
- `gpt-4-turbo-preview` (Recommended)
- `gpt-4`
- `gpt-3.5-turbo`

#### Anthropic
- `claude-3-opus-20240229` (Recommended)
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

#### Google
- `gemini-pro`
- `gemini-pro-vision`

---

## 🧪 Development

### Project Structure

```
fl_js/
├── backend/              # Python FastAPI server
│   ├── __init__.py
│   ├── server.py         # Main FastAPI app
│   ├── websocket.py      # WebSocket connection manager
│   ├── agent.py          # PydanticAI agent setup
│   ├── mcp_server.py     # FastMCP tool definitions
│   ├── callback_router.py # Tool callback routing
│   ├── models.py         # Pydantic models
│   ├── config.py         # Configuration
│   └── utils.py          # Utility functions
│
├── frontend/             # JavaScript UI and tools
│   ├── extension.js      # ComfyUI extension entry
│   ├── chat_ui.js        # Chat sidebar UI
│   ├── ws_client.js      # WebSocket client
│   ├── session_manager.js # Session management
│   ├── tool_executor.js  # Tool execution
│   ├── query_executor.js # Query DSL executor
│   ├── fl_api.js         # FL_JS API wrapper
│   └── diagram_generator.js # Mermaid diagrams
│
├── legacy/               # Original FL_JS code
│   ├── FL_JS.py          # Original node
│   ├── fl_js.js          # Original functions
│   └── NodePackLoader_SideBar.js # Reference
│
├── tests/                # Test suites
│   ├── backend/          # Backend tests
│   ├── frontend/         # Frontend tests
│   └── integration/      # E2E tests
│
├── notes/                # Documentation & plans
│   └── implementation/   # Detailed implementation plans
│
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Python project config
└── README.md             # This file
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/backend/ -v --cov=backend

# Integration tests
pytest tests/integration/ -v

# With coverage report
pytest --cov=backend --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check backend/

# Type checking
mypy backend/

# Formatting
ruff format backend/
```

---

## 📚 Advanced Topics

### Query DSL

The agent uses a JSON-based query language to find and analyze nodes:

```javascript
// Find all KSampler nodes
{
  "filters": {
    "operator": "and",
    "filters": [
      {"field": "type", "operator": "equals", "value": "KSampler"}
    ]
  }
}

// Find checkpoint loaders with specific model
{
  "filters": {
    "operator": "and",
    "filters": [
      {"field": "type", "operator": "equals", "value": "CheckpointLoaderSimple"},
      {"field": "parameters.ckpt_name", "operator": "contains", "value": "sdxl"}
    ]
  }
}

// Traverse downstream from a node
{
  "filters": {
    "operator": "and",
    "filters": [{"field": "id", "operator": "equals", "value": 5}]
  },
  "traversal": {
    "direction": "downstream",
    "max_depth": null  // unlimited
  }
}
```

See `notes/implementation/02_query_dsl.md` for complete documentation.

### Multi-Session Support

Each browser tab gets its own isolated session:
- Unique `session_id` stored in localStorage
- Separate agent instance with independent conversation history
- No message mixing between tabs
- Automatic session cleanup after timeout

### Tool Callback Flow

1. Agent decides to use a tool (e.g., "create_node")
2. Backend sends tool request to frontend via WebSocket
3. Frontend executes FL_JS function
4. Frontend sends result back via WebSocket
5. Backend returns result to agent
6. Agent continues with response

All async, all non-blocking! ⚡

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Workflow

1. Read the implementation plans in `notes/implementation/`
2. Check `notes/implementation/progress.md` for current status
3. Pick a task from the roadmap
4. Write tests first (TDD)
5. Implement the feature
6. Update documentation
7. Submit PR

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **ComfyUI** - The amazing node-based UI for Stable Diffusion
- **PydanticAI** - Modern Python agent framework
- **FastMCP** - Model Context Protocol implementation
- **Mermaid.js** - Beautiful diagram rendering
- Original **FL_JS** - The foundation this builds upon

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/fl_js/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/fl_js/discussions)
- **Documentation**: See `notes/implementation/` for detailed docs

---

## 🗺️ Roadmap

See `notes/roadmap.md` for the full roadmap. Highlights:

- ✅ Multi-session WebSocket support
- ✅ JSON-based query DSL
- ✅ 40+ MCP tools
- ✅ Native ComfyUI sidebar integration
- 🚧 Streaming responses
- 🚧 Workflow templates library
- 🚧 Execution monitoring & feedback loop
- 📋 Plugin system for custom tools
- 📋 Workflow version control
- 📋 Collaborative editing

---

**Built with ❤️ for the ComfyUI community**
