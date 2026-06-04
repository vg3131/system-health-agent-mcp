# cloud_server.py
# FastAPI app — two endpoints:
#   /sse       → Claude Desktop connects here (MCP over SSE)
#   /ws/relay  → relay.py on your Mac connects here (WebSocket)

import asyncio
from fastapi import FastAPI, WebSocket
from mcp.server.fastmcp import FastMCP
import uuid

mcp = FastMCP("system health agent")
app = FastAPI()

relay_ws = None
pending = {}

@app.get("/")
async def health_check():
    return {"status": "ok"}

@app.websocket("/ws/relay")
async def relay(websocket: WebSocket):
    global relay_ws
    await websocket.accept()
    relay_ws = websocket
    try:
        while True:
            data = await websocket.receive_json()
            pending[data["id"]].set_result(data["result"])
    except:
        relay_ws = None

async def call_relay(tool: str, args: dict = {}):
    if relay_ws is None:
        return "Mac relay not connected"
    id = str(uuid.uuid4())
    future = asyncio.get_event_loop().create_future()
    pending[id] = future
    await relay_ws.send_json({"id": id, "tool": tool, "args": args})
    result = await future
    pending.pop(id, None)
    return result

@mcp.tool()
async def get_system_overview():
    """When the user asks what their Mac is doing, wants a general health check, or asks for an overview of system performance.
    This is a overview function which returns every key hardware diagnostic of the system"""
    return await call_relay("get_system_overview")

@mcp.tool()
async def get_top_processes(sort_by: str = "cpu"):
    """When the user asks which apps or processes are using the most CPU or memory, or wants to know what is consuming their resources.
    This returns the ten top processes which are using the most CPU or memory"""
    return await call_relay("get_top_processes", {"sort_by": sort_by})

@mcp.tool()
async def get_memory_detail():
    """When the user asks specifically about RAM or memory usage.
    IMPORTANT: Use ONLY the exact figures returned. Do not recalculate 
    or reinterpret percentages. Present the percent field exactly as given.
    >80% is high, 50-80% is moderate, <50% is healthy."""
    return await call_relay("get_memory_detail")

@mcp.tool()
async def get_cpu_detail():
    """When the user asks specifically about CPU usage, cores, or processor performance. This is to be used when the user only wants information
    on the cpu core performance and details, as well as number of cores and the overall information about the actual CPU hardware on the system"""
    return await call_relay("get_cpu_detail")

@mcp.tool()
async def get_disk_detail():
    """When the user asks specifically about disk or storage usage. This returns information about the read and write information, as well as
    total, used and free disk space. Overall gives information when the user only wants to know about the performance of the system disk"""
    return await call_relay("get_disk_detail")

app.mount("/", mcp.sse_app())