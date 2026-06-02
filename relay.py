# relay.py
# Runs on your Mac — dials out to cloud_server.py via WebSocket
# Listens for tool call requests, executes psutil locally, returns results

import asyncio
import websockets
import psutil
import datetime
import json

def get_system_overview():
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime_seconds = datetime.datetime.now().timestamp() - psutil.boot_time()
    uptime = str(datetime.timedelta(seconds=int(uptime_seconds)))

    return (
        f"System Overview:\n"
        f"CPU Usage: {cpu}%\n"
        f"RAM: {mem.used / 1e9:.1f}GB used of {mem.total / 1e9:.1f}GB ({mem.percent}%)\n"
        f"Disk: {disk.used / 1e9:.1f}GB used of {disk.total / 1e9:.1f}GB ({disk.percent}%)\n"
        f"Uptime: {uptime}"
    )

def get_top_processes(sort_by: str = "cpu"):
    processes = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_percent" if sort_by.lower() == "cpu" else "memory_percent"
    top = sorted(processes, key=lambda x: x[key] or 0, reverse=True)[:10]

    label = "CPU" if key == "cpu_percent" else "Memory"
    result = f"Top 10 processes by {label}:\n"
    for p in top:
        result += f"{p['name']} — {p[key]:.1f}%\n"
    return result

def get_memory_detail():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return (
        f"Memory Detail:\n"
        f"Total RAM: {mem.total / 1e9:.1f}GB\n"
        f"Used: {mem.used / 1e9:.1f}GB ({mem.percent}%)\n"
        f"Available: {mem.available / 1e9:.1f}GB\n"
        f"Swap Used: {swap.used / 1e9:.1f}GB of {swap.total / 1e9:.1f}GB"
    )

def get_cpu_detail():
    overall = psutil.cpu_percent(interval=1)
    per_core = psutil.cpu_percent(interval=1, percpu=True)
    freq = psutil.cpu_freq()
    result = f"CPU Detail:\n"
    result += f"Overall: {overall}%\n"
    result += f"Frequency: {freq.current:.0f}MHz (max {freq.max:.0f}MHz)\n"
    result += f"Cores ({len(per_core)}):\n"
    for i, c in enumerate(per_core):
        result += f"  Core {i+1}: {c}%\n"
    return result

def get_disk_detail():
    disk = psutil.disk_usage('/')
    io = psutil.disk_io_counters()
    return (
        f"Disk Detail:\n"
        f"Total: {disk.total / 1e9:.1f}GB\n"
        f"Used: {disk.used / 1e9:.1f}GB ({disk.percent}%)\n"
        f"Free: {disk.free / 1e9:.1f}GB\n"
        f"Reads since boot: {io.read_bytes / 1e9:.1f}GB\n"
        f"Writes since boot: {io.write_bytes / 1e9:.1f}GB"
    )

handlers = {
    "get_system_overview": get_system_overview,
    "get_top_processes": get_top_processes,
    "get_memory_detail": get_memory_detail,
    "get_cpu_detail": get_cpu_detail,
    "get_disk_detail": get_disk_detail
}

async def main():
    async with websockets.connect("wss://web-production-b4b1a.up.railway.app/ws/relay") as ws:
        while True:
            message = json.loads(await ws.recv())
            result = handlers[message["tool"]](**message["args"])
            await ws.send(json.dumps({"id": message["id"], "result": result}))
            
asyncio.run(main())
