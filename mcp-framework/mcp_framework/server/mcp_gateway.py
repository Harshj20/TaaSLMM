"""MCP Gateway - HTTP-SSE server implementing MCP protocol."""

import asyncio
import json
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import structlog

from mcp_framework.server.tool_registry import get_tool_registry
from mcp_framework.server.workflow_executor import WorkflowExecutor
from mcp_framework.storage.database import init_database
from mcp_framework.config import settings

# Initialize logger
logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(title="MCP Framework Gateway", version="0.1.0")

# Initialize components
tool_registry = get_tool_registry()
workflow_executor = WorkflowExecutor()


class MCPRequest(BaseModel):
    """MCP protocol request."""
    method: str
    params: Dict[str, Any] = {}


class MCPResponse(BaseModel):
    """MCP protocol response."""
    result: Any = None
    error: str = None


class ToolCallRequest(BaseModel):
    """Tool call request."""
    name: str
    arguments: Dict[str, Any]


class WorkflowRequest(BaseModel):
    """Workflow execution request."""
    dag: Dict[str, Any]
    user_id: str = "anonymous"


@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    logger.info("Starting MCP Gateway")
    init_database()
    logger.info(f"Registered {len(tool_registry.list_tools())} tools")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-gateway"}


@app.get("/mcp/tools")
async def list_tools(category: str = None):
    """
    List available tools (MCP tools/list).
    
    Args:
        category: Optional category filter (UTILITY, TRAINING, ADMIN)
    
    Returns:
        List of tool metadata
    """
    try:
        from mcp_framework.tools.base import ToolCategory
        
        cat_filter = ToolCategory(category) if category else None
        tool_names = tool_registry.list_tools(category=cat_filter)
        
        tools = []
        for name in tool_names:
            metadata = tool_registry.get_metadata(name)
            if metadata:
                tools.append({
                    "name": metadata.name,
                    "description": metadata.description,
                    "category": metadata.category.value,
                    "inputSchema": metadata.input_schema,
                    "outputSchema": metadata.output_schema,
                    "requiresIsolation": metadata.requires_isolation,
                    "dependencies": metadata.dependencies
                })
        
        return {"tools": tools, "count": len(tools)}
    
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/call")
async def call_tool(request: ToolCallRequest):
    """
    Execute a single tool (MCP tools/call).
    
    Args:
        request: Tool call request with name and arguments
    
    Returns:
        Tool execution result
    """
    try:
        tool_class = tool_registry.get_tool(request.name)
        
        if tool_class is None:
            raise HTTPException(status_code=404, detail=f"Tool '{request.name}' not found")
        
        # Execute tool
        tool_instance = tool_class()
        result = await tool_instance.execute(request.arguments)
        
        return {
            "tool": request.name,
            "status": "COMPLETED",
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Error executing tool {request.name}: {e}")
        return {
            "tool": request.name,
            "status": "FAILED",
            "error": str(e)
        }


@app.post("/mcp/workflow")
async def execute_workflow(request: WorkflowRequest):
    """
    Execute a workflow DAG.
    
    Args:
        request: Workflow execution request
    
    Returns:
        StreamingResponse with execution progress
    """
    try:
        # Execute workflow with streaming
        async def event_stream():
            """Stream workflow execution events."""
            try:
                async for event in workflow_executor.execute_streaming(
                    request.dag,
                    user_id=request.user_id
                ):
                    yield f"data: {json.dumps(event)}\n\n"
                
                # Final completion event
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
            except Exception as e:
                error_event = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_event)}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """
    Get workflow execution status.
    
    Args:
        workflow_id: Workflow execution ID
    
    Returns:
        Workflow status and progress
    """
    try:
        from mcp_framework.storage.database import get_db_manager
        from mcp_framework.storage.models import WorkflowExecution
        
        db_manager = get_db_manager()
        
        with db_manager.get_session() as session:
            workflow = session.query(WorkflowExecution).filter_by(id=workflow_id).first()
            
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            return {
                "workflow_id": workflow.id,
                "status": workflow.status,
                "progress": workflow.progress,
                "created_at": workflow.created_at.isoformat(),
                "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "error": workflow.error_message,
                "results": workflow.results
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the MCP Gateway server."""
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
