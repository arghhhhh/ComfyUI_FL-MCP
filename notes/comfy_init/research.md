# ComfyUI Backend Server Auto-Start Research

**Date:** 2025-10-14  
**Purpose:** Investigate how to automatically start FL_JS FastAPI backend server when ComfyUI initializes

---

## Problem Statement

Currently, users must manually start the FL_JS backend server:
```bash
cd backend
python server.py
```

This is a poor user experience. We need the backend to start automatically when ComfyUI loads the custom node.

---

## Research Questions

1. **When does ComfyUI execute `__init__.py`?**
2. **Can we start background processes from `__init__.py`?**
3. **How do we ensure clean shutdown when ComfyUI exits?**
4. **Are there existing examples of custom nodes running background servers?**
5. **Should we containerize the backend (Docker)?**

---

## Findings

### 1. ComfyUI Custom Node Lifecycle

**Source:** [ComfyUI Official Docs - Lifecycle](https://docs.comfy.org/custom-nodes/backend/lifecycle)

#### Loading Process
1. ComfyUI scans `custom_nodes/` directory on startup
2. For each directory, imports the module (executes `__init__.py`)
3. Looks for `NODE_CLASS_MAPPINGS` export
4. If found, registers the custom node
5. If `WEB_DIRECTORY` is defined, serves JavaScript files

#### Execution Timing
- `__init__.py` is executed **once** during ComfyUI startup
- Happens **before** the web UI is available
- Errors in `__init__.py` cause the module to fail loading (but ComfyUI continues)

#### Key Insight
> ⚠️ **`__init__.py` runs at module import time** - This is the perfect place to start background servers!

---

### 2. Background Process Management - Real-World Example

**Source:** [ComfyUI-NODEJS by daxcay](https://github.com/daxcay/ComfyUI-NODEJS)

This custom node successfully runs Node.js servers alongside ComfyUI. Here's how they do it:

#### Architecture
```
ComfyUI-NODEJS/
├── __init__.py              # Module entry point
├── classes/
│   ├── NodeInstaller.py    # Manages Node.js installation
│   └── NodeScriptRunner.py # Subprocess management
├── nodejs/                 # Node.js projects directory
│   ├── project1/
│   │   ├── package.json
│   │   └── app.js
│   └── project2/
└── config.py
```

#### Implementation Pattern

**Step 1: `__init__.py` orchestrates startup**
```python
import os
from .classes.NodeScriptRunner import NodeScriptRunner

NODE_JS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nodejs")

# Create script runner
nodeScriptRunner = NodeScriptRunner()

# Scan for projects and add them
for project_name, project_info in projects.items():
    production_script = project_info['production']
    if production_script:
        nodeScriptRunner.add(
            os.path.join(NODE_JS_FOLDER, project_name),
            production_script.split()
        )

# Start all servers
nodeScriptRunner.run()

# Export mappings (can be empty!)
NODE_CLASS_MAPPINGS = {}
```

**Step 2: `NodeScriptRunner` manages subprocesses**
```python
import subprocess
import atexit

class NodeScriptRunner:
    def __init__(self):
        self.scripts = []
        self.processes = []
        self.should_run = True
    
    def add(self, cwd, script):
        """Add a script to be run"""
        self.scripts.append((cwd, script))
    
    def start_script(self, cwd, script):
        """Start a subprocess"""
        process = subprocess.Popen(
            script,
            cwd=cwd,
            stdout=None,  # Inherit stdout
            stderr=None   # Inherit stderr
        )
        self.processes.append((process, cwd, script))
        print(f"Project script '{script}' in '{cwd}' started.")
        return process
    
    def run(self):
        """Start all scripts"""
        for cwd, script in self.scripts:
            self.start_script(cwd, script)
    
    def terminate_background_js(self):
        """Cleanup: terminate all subprocesses"""
        self.should_run = False
        for process, cwd, script in self.processes:
            if process:
                process.terminate()
                print(f"Project script '{script}' in '{cwd}' terminated.")
    
    def __del__(self):
        """Destructor: cleanup on garbage collection"""
        self.terminate_background_js()
```

#### Key Techniques

1. **subprocess.Popen** - Non-blocking process spawning
   - `cwd=` sets working directory
   - `stdout=None, stderr=None` inherits parent's streams (logs to ComfyUI console)
   - Process runs in background

2. **`__del__` method** - Cleanup on object destruction
   - Called when Python garbage collects the object
   - Ensures processes are terminated
   - Acts like `atexit` but object-scoped

3. **Module-level execution** - Code runs at import time
   - `__init__.py` creates global instances
   - Instances persist for lifetime of ComfyUI process
   - Cleanup happens when ComfyUI exits

---

### 3. Subprocess Management Best Practices

#### Option A: Using `__del__` (ComfyUI-NODEJS approach)
```python
class ServerRunner:
    def __del__(self):
        self.cleanup()
```
**Pros:**
- Simple
- Object-scoped
- Automatic

**Cons:**
- Timing is non-deterministic (depends on garbage collection)
- May not run if Python crashes
- Not guaranteed to run in all scenarios

#### Option B: Using `atexit` (More robust)
```python
import atexit

class ServerRunner:
    def __init__(self):
        atexit.register(self.cleanup)
    
    def cleanup(self):
        # Terminate processes
        pass
```
**Pros:**
- Guaranteed to run on normal exit
- More predictable timing
- Standard Python pattern

**Cons:**
- Doesn't run on SIGKILL or crash
- Still not perfect for all scenarios

#### Option C: Hybrid Approach (Best)
```python
import atexit

class ServerRunner:
    def __init__(self):
        self._cleaned_up = False
        atexit.register(self.cleanup)
    
    def cleanup(self):
        if self._cleaned_up:
            return
        self._cleaned_up = True
        # Terminate processes
    
    def __del__(self):
        self.cleanup()
```
**Pros:**
- Double safety (atexit + __del__)
- Idempotent cleanup
- Best of both worlds

**Cons:**
- Slightly more complex

---

### 4. Should We Containerize? (Docker)

#### Arguments For Docker:
- ✅ Isolated environment
- ✅ Dependency management
- ✅ Consistent across systems
- ✅ Easy to version control

#### Arguments Against Docker:
- ❌ **Overkill** for a simple FastAPI server
- ❌ Adds complexity for users
- ❌ Requires Docker installation
- ❌ ComfyUI custom nodes typically don't use containers
- ❌ Harder to debug (extra layer of abstraction)
- ❌ Port mapping complexity
- ❌ Volume mounting for logs

#### Verdict: **NO Docker** (for now)

**Reasoning:**
1. FastAPI is lightweight and easy to run directly
2. Python dependencies already managed via `requirements.txt`
3. Follows ComfyUI custom node conventions
4. Simpler user experience
5. Easier to debug
6. Can add Docker as optional deployment method later

**Alternative:** Subprocess approach like ComfyUI-NODEJS

---

### 5. Process Output Handling

#### Option A: Inherit stdout/stderr (Simplest)
```python
subprocess.Popen(
    ["python", "server.py"],
    cwd=backend_dir,
    stdout=None,  # Inherit
    stderr=None   # Inherit
)
```
**Pros:**
- Server logs appear in ComfyUI console
- No extra code needed
- Easy to debug

**Cons:**
- Mixed logs (ComfyUI + FL_JS)
- Can't filter or redirect easily

#### Option B: Pipe to file
```python
log_file = open("fl_js_backend.log", "w")
subprocess.Popen(
    ["python", "server.py"],
    cwd=backend_dir,
    stdout=log_file,
    stderr=log_file
)
```
**Pros:**
- Separate log file
- Can review later
- Cleaner ComfyUI console

**Cons:**
- Need to manage file handle
- Users might not find logs
- File handle must stay open

#### Option C: DEVNULL (Silent)
```python
import subprocess

subprocess.Popen(
    ["python", "server.py"],
    cwd=backend_dir,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
```
**Pros:**
- Clean console
- No file management

**Cons:**
- **Can't debug!**
- Silent failures
- Bad user experience

#### Verdict: **Option A (Inherit)** for development, **Option B (File)** for production

---

## Recommended Approach for FL_JS

### Architecture

```
FL_JS/
├── __init__.py              # Starts backend on import
├── backend/
│   ├── server.py         # FastAPI app
│   ├── server_runner.py  # NEW: Subprocess manager
│   └── ...
├── web/js/
└── ...
```

### Implementation Plan

1. **Create `backend/server_runner.py`**
   - Class to manage FastAPI subprocess
   - Uses `subprocess.Popen`
   - Hybrid cleanup (`atexit` + `__del__`)
   - Configurable output handling

2. **Update `__init__.py`**
   - Import `ServerRunner`
   - Create global instance
   - Start server on import
   - Export NODE_CLASS_MAPPINGS (empty dict)

3. **Configuration**
   - Add `AUTO_START_BACKEND` to config
   - Allow users to disable if needed
   - Default: enabled

4. **Error Handling**
   - Check if port is already in use
   - Graceful failure (don't crash ComfyUI)
   - Clear error messages

---

## Implementation Details

### Python Executable Detection

**Problem:** Which Python interpreter to use?

**Solution:** Use `sys.executable` (same Python running ComfyUI)
```python
import sys

python_executable = sys.executable
subprocess.Popen([python_executable, "server.py"], ...)
```

### Port Conflict Detection

**Problem:** What if port 8000 is already in use?

**Solution:** Check before starting
```python
import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if is_port_in_use(8000):
    print("[FL_JS] Port 8000 already in use. Backend not started.")
    return
```

### Health Check

**Problem:** How do we know the server started successfully?

**Solution:** Poll the health endpoint
```python
import time
import requests

def wait_for_server(url, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(f"{url}/health")
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

if wait_for_server("http://localhost:8000"):
    print("[FL_JS] Backend server started successfully!")
else:
    print("[FL_JS] Backend server failed to start.")
```

---

## Security Considerations

### 1. Subprocess Security
- ✅ Use list form: `["python", "server.py"]` not shell string
- ✅ Avoids shell injection vulnerabilities
- ✅ No `shell=True` parameter

### 2. Port Binding
- ⚠️ Backend binds to `0.0.0.0` (all interfaces)
- 🔒 Consider binding to `127.0.0.1` (localhost only)
- 🔒 Add authentication layer (future)

### 3. Process Isolation
- ✅ Backend runs as separate process
- ✅ Can't directly access ComfyUI memory
- ✅ Communication only via WebSocket

---

## Alternative: Embedded Server (Not Recommended)

**Idea:** Run FastAPI in a background thread instead of subprocess

```python
import threading
import uvicorn

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
```

**Pros:**
- No subprocess management
- Same Python process
- Easier to share state

**Cons:**
- ❌ Harder to isolate
- ❌ Can't easily restart
- ❌ Shared memory space (crash affects ComfyUI)
- ❌ Thread safety issues
- ❌ Daemon threads don't clean up properly
- ❌ Uvicorn not designed for thread usage

**Verdict:** Stick with subprocess approach

---

## Testing Strategy

### Manual Testing
1. Start ComfyUI
2. Check console for `[FL_JS] Backend server started`
3. Open browser console, verify WebSocket connection
4. Stop ComfyUI
5. Verify backend process terminated (no zombie processes)

### Automated Testing
1. Unit tests for `ServerRunner` class
2. Integration test: start/stop lifecycle
3. Test port conflict handling
4. Test cleanup on various exit scenarios

---

## Open Questions

1. **Should we support custom ports?**
   - Default: 8000
   - Allow override via `.env`?
   - Frontend needs to know the port

2. **What if backend crashes during runtime?**
   - Auto-restart like ComfyUI-NODEJS?
   - Or just log error and let user restart ComfyUI?
   - Monitoring thread adds complexity

3. **Windows vs Unix differences?**
   - Process termination signals
   - Path separators
   - Python executable detection

4. **Should we bundle backend as executable?**
   - PyInstaller to create standalone binary?
   - Would eliminate Python dependency issues
   - Much more complex build process

---

## Conclusion

**Recommended Solution:**

1. ✅ Use subprocess.Popen to start FastAPI backend
2. ✅ Hybrid cleanup (atexit + __del__)
3. ✅ Inherit stdout/stderr for debugging
4. ✅ Port conflict detection
5. ✅ Health check with timeout
6. ✅ Configurable via .env
7. ❌ No Docker (for now)
8. ❌ No auto-restart (keep it simple)
9. ❌ No embedded server (use subprocess)

**Next Steps:**
1. Create `backend/server_runner.py`
2. Update `__init__.py` to use ServerRunner
3. Add health check endpoint to backend
4. Test on Windows, Linux, macOS
5. Update documentation

---

## References

- [ComfyUI Custom Node Lifecycle](https://docs.comfy.org/custom-nodes/backend/lifecycle)
- [ComfyUI-NODEJS Implementation](https://github.com/daxcay/ComfyUI-NODEJS)
- [Python subprocess Documentation](https://docs.python.org/3/library/subprocess.html)
- [Python atexit Documentation](https://docs.python.org/3/library/atexit.html)
