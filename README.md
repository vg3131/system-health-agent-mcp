# system-health-agent-mcp

A hosted MCP server that lets anyone query live hardware stats from your Mac via Claude Desktop.

---

## How it works

```
Claude Desktop → Hosted MCP Server (Railway) ↔ relay.py on your Mac → psutil → hardware
```

- **`cloud_server.py`** — deployed to Railway. Exposes 5 MCP tools over SSE for Claude Desktop, and holds a WebSocket connection to your Mac. When Claude calls a tool, it forwards the request to the relay and returns the result.
- **`relay.py`** — runs on your Mac. Dials out to the cloud server, listens for tool call requests, executes psutil locally, and sends results back.

---

## Tools

| Tool | Description |
|------|-------------|
| `get_system_overview` | CPU, RAM, disk, and uptime at a glance |
| `get_top_processes` | Top 10 processes by CPU or memory |
| `get_cpu_detail` | Per-core breakdown and frequency |
| `get_memory_detail` | RAM and swap usage |
| `get_disk_detail` | Disk space and read/write since boot |

---

## Stack

- **FastAPI** + **FastMCP** — cloud server and MCP protocol
- **websockets** — relay connection between cloud and Mac
- **psutil** — reads live hardware data from macOS
- **Railway** — hosts the cloud server
