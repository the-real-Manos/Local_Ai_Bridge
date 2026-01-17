# """
# Created by https://github.com/the-real-Manos
# Chat Bridge: Allows LM studio to communicate via locally hosted webpage.
# Connects to LM Studio via port 1234 (configurable).
# """

import uvicorn
import socket
import httpx
import os
import sys
import json
import qrcode
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict

# --- CONFIGURATION ---
DEFAULT_LM_PORT = 1234
HOST_PORT = 8000
sessions: Dict[str, List[Dict[str, str]]] = {}

app = FastAPI()

# Global variable to store the discovered LM Studio URL
target_lm_studio_url = None

def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def get_path(relative_path: str) -> str:
    """Resolves file paths for PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def print_qr_code(url: str):
    try:
        qr = qrcode.QRCode(version=1, box_size=1, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii()
    except Exception as e:
        print(f"[!] Could not generate QR code: {e}")

async def discover_lm_studio():
    global target_lm_studio_url
    candidates = [
        f"http://localhost:{DEFAULT_LM_PORT}",
        f"http://127.0.0.1:{DEFAULT_LM_PORT}",
        f"http://{get_lan_ip()}:{DEFAULT_LM_PORT}"
    ]
    
    print("[*] Searching for LM Studio...")
    async with httpx.AsyncClient() as client:
        for base_url in candidates:
            try:
                response = await client.get(f"{base_url}/v1/models", timeout=1.5)
                if response.status_code == 200:
                    target_lm_studio_url = f"{base_url}/v1/chat/completions"
                    print(f"[+] Found LM Studio at: {base_url}")
                    return
            except Exception:
                continue
    print("[!] Warning: LM Studio not found. Bridge will retry on next request.")

@app.on_event("startup")
async def startup_event():
    await discover_lm_studio()

@app.get("/", response_class=HTMLResponse)
async def index():
    # Looks for index.html in a 'static' folder next to the executable/script
    try:
        with open(get_path("static/index.html"), "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<h1>Error</h1><p>Could not load static/index.html. Ensure the file exists.</p><p>Details: {e}</p>"

@app.get("/health")
async def health():
    global target_lm_studio_url
    if not target_lm_studio_url:
        return {"status": "offline", "reason": "No URL discovery"}

    try:
        base_url = target_lm_studio_url.replace("/v1/chat/completions", "")
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{base_url}/v1/models", timeout=1.0)
            return {"status": "online" if resp.status_code == 200 else "offline"}
    except Exception:
        return {"status": "offline"}

@app.post("/chat")
async def chat(request: Request):
    global target_lm_studio_url
    if not target_lm_studio_url:
        await discover_lm_studio()
        if not target_lm_studio_url:
            return {"error": "LM Studio not found. Ensure the server is running."}
    
    try:
        data = await request.json()
    except Exception:
        return {"error": "Invalid JSON"}

    session_id = data.get("session_id", "default_guest")
    incoming_messages = data.get("messages", [])
    
    if not incoming_messages:
        return {"error": "No messages provided"}

    user_message = incoming_messages[-1]
    if session_id not in sessions:
        sessions[session_id] = []
        # Optional System Prompt
        # sessions[session_id].append({"role": "system", "content": "You are a helpful assistant."})

    sessions[session_id].append(user_message)

    payload = {
        "messages": sessions[session_id],
        "stream": True,
        "temperature": 0.7
    }

    async def event_generator():
        full_ai_response = ""
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", target_lm_studio_url, json=payload) as r:
                    async for line in r.aiter_lines():
                        if line.startswith("data: "):
                            yield f"{line}\n\n"
                            if "[DONE]" in line: continue
                            try:
                                json_str = line.replace("data: ", "").strip()
                                chunk_data = json.loads(json_str)
                                delta = chunk_data["choices"][0].get("delta", {}).get("content", "")
                                full_ai_response += delta
                            except Exception:
                                pass
            
            if full_ai_response:
                sessions[session_id].append({"role": "assistant", "content": full_ai_response})

        except Exception as e:
            yield f"data: {{\"error\": \"Connection failed: {str(e)}\"}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    lan_ip = get_lan_ip()
    url = f"http://{lan_ip}:{HOST_PORT}"
    
    print(f"\n" + "="*40)
    print(f"AI CHAT BRIDGE ACTIVE")
    print(f"Server IP: {lan_ip}")
    print(f"Port: {HOST_PORT}")
    print(f"-"*40)
    print(f"SCAN TO CONNECT:")
    print_qr_code(url)
    print(f"Or visit: {url}")
    print(f"="*40 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=HOST_PORT, log_level="warning")