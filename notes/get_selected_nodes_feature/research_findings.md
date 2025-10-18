# Research: Get Selected Nodes Feature for FL_Agent

## Overview
Researching the feasibility of adding a `get_current_user_focus()` tool to `backend/mcp_server.py` that returns JSON data for currently selected nodes in ComfyUI. This would provide context-aware assistance when users discuss specific workflow nodes.

## Current Architecture

### Frontend: `web/js/fl_api.js`
- Already has a `select()` method that can SELECT nodes
- Does NOT currently have a method to GET selected nodes
- Uses ComfyUI's `app.canvas` API for node selection

### Backend: `backend/mcp_server.py`
- Uses WebSocket-based tool execution via `MCPWebSocketClient`
- Tools execute frontend functions through the callback mechanism
- Would need a new tool definition: `get_current_user_focus()`

## ComfyUI Selected Nodes API

### Access Pattern
Based on ComfyUI official documentation:

```javascript
// Access selected nodes object
const selectedNodes = app.canvas.selected_nodes;

// Structure: Object where keys are node IDs, values are ComfyNode objects
{
  "nodeId1": ComfyNode_object1,
  "nodeId2": ComfyNode_object2
}
```

### Selected Node Properties
Each selected node object contains:
- `id` - Node ID
- `title` - Node title
- `type` - Node type/class (e.g., "KSampler")
- `pos` - Position `[x, y]`
- `size` - Size `[width, height]`
- `mode` - Node mode (0=normal, 2=muted, 4=bypassed)
- `widgets` - Array of widget objects with parameters
- `inputs` - Array of input slots
- `outputs` - Array of output slots

### Iteration Pattern
```javascript
Object.values(app.canvas.selected_nodes).forEach(node => {
  console.log(node.title, node.id);
});
```

## Implementation Design

### 1. Frontend Addition to `web/js/fl_api.js`

Add a new method to the `FL_API` class:

```javascript
/**
 * Get currently selected nodes with their full data
 * @returns {Array<object>} Array of selected node data objects
 */
getSelectedNodes() {
    try {
        const selectedNodes = app.canvas.selected_nodes;
        const result = [];
        
        for (const nodeId in selectedNodes) {
            const node = selectedNodes[nodeId];
            
            // Extract widget values
            const parameters = {};
            if (node.widgets) {
                for (const widget of node.widgets) {
                    parameters[widget.name] = widget.value;
                }
            }
            
            // Extract input/output slot info
            const inputs = node.inputs ? node.inputs.map(input => ({
                name: input.name,
                type: input.type,
                link: input.link
            })) : [];
            
            const outputs = node.outputs ? node.outputs.map(output => ({
                name: output.name,
                type: output.type,
                links: output.links
            })) : [];
            
            result.push({
                id: node.id,
                title: node.title,
                type: node.type,
                position: { x: node.pos[0], y: node.pos[1] },
                size: { width: node.size[0], height: node.size[1] },
                mode: node.mode,
                parameters: parameters,
                inputs: inputs,
                outputs: outputs
            });
        }
        
        console.log(`[FL_API] Retrieved ${result.length} selected node(s)`);
        return result;
    } catch (error) {
        console.error("[FL_API] getSelectedNodes error:", error);
        throw error;
    }
}
```

### 2. Tool Executor Integration

The `web/js/tool_executor.js` would need to handle this new tool. Based on the existing pattern, it likely already supports this through the dynamic tool mapping.

### 3. Backend MCP Server Addition

Add to `backend/mcp_server.py`:

```python
class GetCurrentUserFocusRequest(BaseModel):
    """Request to get currently selected nodes (user focus)."""
    pass

@mcp.tool()
async def get_current_user_focus(request: GetCurrentUserFocusRequest, ctx: Context) -> Dict[str, Any]:
    """Get currently selected nodes in ComfyUI to understand user's current focus.
    
    This tool provides context-aware assistance by returning detailed information
    about the nodes the user currently has selected in the workflow canvas.
    
    USE CASES:
    - User asks "what does this node do?" - Check selected nodes for context
    - User says "change the seed" - Find seed parameter in selected nodes
    - User requests modifications - Know which nodes they're referring to
    - Debugging assistance - Analyze parameters of nodes user is examining
    
    RETURNS:
    - Array of selected node objects with:
      - Node ID, title, type
      - Position and size
      - All parameter values
      - Input/output connections
      - Node mode (normal/muted/bypassed)
    
    AGENT WORKFLOW:
    1. User mentions "this node" or "these nodes" - Call this tool
    2. Extract relevant info from selected nodes
    3. Provide context-aware response
    """
    return await _execute_tool(ctx, "get_selected_nodes", {})
```

## Use Case Examples

### Scenario 1: User Asks About Selected Node
```
User: "What does this node do?"
Agent: [Calls get_current_user_focus()]
Agent: "You have a KSampler node selected. This node performs the diffusion sampling process..."
```

### Scenario 2: User Wants to Modify Parameters
```
User: "Change the seed to something random"
Agent: [Calls get_current_user_focus()]
Agent: [Finds KSampler with seed parameter in selected nodes]
Agent: [Calls set_node_values() with new random seed]
```

### Scenario 3: Debugging Context
```
User: "Why isn't this working?"
Agent: [Calls get_current_user_focus()]
Agent: "I see you have a CheckpointLoader selected with model 'sd_xl_base_1.0.safetensors'..."
```

## Technical Considerations

### 1. Empty Selection Handling
- Should return empty array `[]` when no nodes selected
- Agent should handle gracefully and ask for clarification

### 2. Large Selection Performance
- Selecting many nodes (50+) could create large JSON payloads
- Consider adding optional limit parameter
- Or return summary vs. full details

### 3. Widget Data Serialization
- Some widget values might be complex objects
- Need to ensure JSON serialization works
- May need custom serialization for certain widget types

### 4. Connection Information
- Input/output links reference other nodes
- Could optionally include connected node info
- Trade-off between detail and payload size

## Implementation Steps

1. **Add method to `web/js/fl_api.js`**
   - Implement `getSelectedNodes()` method
   - Test in browser console

2. **Verify tool executor support**
   - Check if `web/js/tool_executor.js` needs updates
   - Likely already handles this through dynamic mapping

3. **Add MCP tool to `backend/mcp_server.py`**
   - Define `GetCurrentUserFocusRequest` model
   - Implement `get_current_user_focus()` tool
   - Map to frontend `get_selected_nodes` tool

4. **Test end-to-end**
   - Select nodes in ComfyUI
   - Call tool from MCP client
   - Verify JSON response structure

5. **Document usage**
   - Add examples to README
   - Document expected response format

## Alternative Approaches

### Option A: Return Full Node Serialization
- Pros: Complete context, includes all node data
- Cons: Large payloads, may include unnecessary data

### Option B: Return Summary Only
- Pros: Lightweight, faster
- Cons: May need follow-up calls for details
- Could use existing `find_node()` or `get_node_values()` for details

### Option C: Configurable Detail Level
```python
class GetCurrentUserFocusRequest(BaseModel):
    include_parameters: bool = True
    include_connections: bool = True
    include_position: bool = False
```

**Recommendation:** Start with Option A (full data), optimize later if needed.

## Security Considerations

- No security issues - read-only operation
- No file system access
- No external network calls
- Safe to expose to agent

## Related Files

- `web/js/fl_api.js` - Frontend API wrapper (needs new method)
- `web/js/tool_executor.js` - Tool execution handler (verify support)
- `backend/mcp_server.py` - MCP tool definitions (needs new tool)
- `backend/models.py` - Request models (may need new model)

## References

- [ComfyUI Official Docs - LGraphCanvas](https://docs.comfy.org/custom-nodes/js/javascript_objects_and_hijacking)
- [LiteGraph.js GitHub](https://github.com/jagenjo/litegraph.js)
- ComfyUI source: `/scripts/app.js` (canvas implementation)

## Next Steps

1. Review this research with user
2. Confirm implementation approach
3. Switch to **Implementation Mode** if approved
4. Begin coding the feature

---

**Research Status:** Complete ✅  
**Recommendation:** Feature is feasible and valuable. Implementation straightforward.  
**Estimated Effort:** 1-2 hours (frontend method + backend tool + testing)
