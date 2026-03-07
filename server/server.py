"""
Maestra Fleet Manager Server
FastAPI server for multi-device state sync and video relay.
Deploy to Railway, Render, or any Python hosting.

Krista Faist | 2026 | MIT License
Based on Maestra by Jordan Snyder / Meow Wolf (MIT)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json
import time
import uuid
import asyncio
from typing import Dict, Optional
from datetime import datetime

app = FastAPI(title="Maestra Fleet Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# IN-MEMORY STATE
# ============================================================

entities: Dict[str, dict] = {}
entity_types: Dict[str, dict] = {}
ws_connections: list = []

video_frames = {}

def get_room_frames(room: str = "room1"):
    if room not in video_frames:
        video_frames[room] = {
            "browser": {"data": None, "timestamp": 0},
            "td": {"data": None, "timestamp": 0},
        }
    return video_frames[room]

# ============================================================
# ENTITY MANAGEMENT
# ============================================================

@app.get("/entities")
async def list_entities():
    return list(entities.values())

@app.get("/entities/by-slug/{slug}")
async def get_entity_by_slug(slug: str):
    for e in entities.values():
        if e.get("slug") == slug:
            return e
    return JSONResponse({"error": "not found"}, status_code=404)

@app.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    if entity_id in entities:
        return entities[entity_id]
    return JSONResponse({"error": "not found"}, status_code=404)

@app.get("/entities/{entity_id}/state")
async def get_entity_state(entity_id: str):
    if entity_id in entities:
        return {"state": entities[entity_id].get("state", {})}
    return JSONResponse({"error": "not found"}, status_code=404)

@app.patch("/entities/{entity_id}/state")
async def update_entity_state(entity_id: str, request: Request):
    body = await request.json()
    if entity_id not in entities:
        return JSONResponse({"error": "not found"}, status_code=404)
    new_state = body.get("state", {})
    source = body.get("source", "unknown")
    entities[entity_id]["state"].update(new_state)
    msg = json.dumps({
        "type": "state_changed",
        "entity_id": entity_id,
        "entity_slug": entities[entity_id].get("slug", ""),
        "current_state": entities[entity_id]["state"],
        "changed_keys": list(new_state.keys()),
        "source": source,
        "timestamp": time.time()
    })
    for ws in ws_connections[:]:
        try:
            await ws.send_text(msg)
        except:
            ws_connections.remove(ws)
    return {"status": "ok"}

@app.post("/entities/types")
async def create_entity_type(request: Request):
    body = await request.json()
    type_id = str(uuid.uuid4())
    entity_types[type_id] = {
        "id": type_id,
        "name": body.get("name", ""),
        "display_name": body.get("display_name", ""),
        "description": body.get("description", ""),
        "default_state": body.get("default_state", {}),
    }
    return entity_types[type_id]

@app.post("/entities")
async def create_entity(request: Request):
    body = await request.json()
    entity_id = str(uuid.uuid4())
    entity = {
        "id": entity_id,
        "name": body.get("name", ""),
        "slug": body.get("slug", ""),
        "entity_type_id": body.get("entity_type_id", ""),
        "parent_id": body.get("parent_id"),
        "state": body.get("state", {}),
        "description": body.get("description", ""),
        "tags": body.get("tags", []),
        "metadata": body.get("metadata", {}),
        "device_id": body.get("device_id"),
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
    }
    entities[entity_id] = entity
    return entity

# ============================================================
# NLP / TRANSCRIPT
# ============================================================

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    HAS_SPACY = True
except:
    HAS_SPACY = False

@app.post("/transcript")
async def process_transcript(request: Request):
    body = await request.json()
    text = body.get("text", "")
    source = body.get("source", "unknown")
    if not text.strip():
        return {"status": "ignored", "reason": "empty"}
    p5 = text.strip()
    p6 = text.strip()
    if HAS_SPACY:
        doc = nlp(text)
        nouns = [chunk.text for chunk in doc.noun_chunks]
        if nouns:
            p5 = nouns[-1]
    for e in entities.values():
        e["state"]["p5"] = p5
        e["state"]["p6"] = p6
        e["state"]["sd_prompt"] = p5
    msg = json.dumps({
        "type": "state_changed",
        "entity_slug": "all",
        "current_state": {"p5": p5, "p6": p6},
        "source": source,
        "timestamp": time.time()
    })
    for ws in ws_connections[:]:
        try:
            await ws.send_text(msg)
        except:
            ws_connections.remove(ws)
    return {"status": "ok", "p5": p5, "p6": p6}

# ============================================================
# VIDEO FRAME RELAY
# ============================================================

@app.post("/video/frame/browser")
async def post_browser_frame(request: Request, room: str = "room1"):
    data = await request.body()
    frames = get_room_frames(room)
    frames["browser"]["data"] = data
    frames["browser"]["timestamp"] = time.time()
    return Response(status_code=200)

@app.get("/video/frame/browser")
async def get_browser_frame(room: str = "room1"):
    frames = get_room_frames(room)
    f = frames["browser"]
    if f["data"] and (time.time() - f["timestamp"]) < 5:
        return Response(content=f["data"], media_type="image/jpeg")
    return Response(status_code=204)

@app.post("/video/frame/td")
async def post_td_frame(request: Request, room: str = "room1"):
    data = await request.body()
    frames = get_room_frames(room)
    frames["td"]["data"] = data
    frames["td"]["timestamp"] = time.time()
    return Response(status_code=200)

@app.get("/video/frame/td")
async def get_td_frame(room: str = "room1"):
    frames = get_room_frames(room)
    f = frames["td"]
    if f["data"] and (time.time() - f["timestamp"]) < 5:
        return Response(content=f["data"], media_type="image/jpeg")
    return Response(status_code=204)

@app.get("/video/status")
async def video_status(room: str = "room1"):
    now = time.time()
    frames = get_room_frames(room)
    b = frames["browser"]
    t = frames["td"]
    return {
        "room": room,
        "browser": b["data"] is not None and (now - b["timestamp"]) < 5,
        "browser_age": round(now - b["timestamp"], 1) if b["data"] else None,
        "td": t["data"] is not None and (now - t["timestamp"]) < 5,
        "td_age": round(now - t["timestamp"], 1) if t["data"] else None,
    }

# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "state_update":
                    slug = msg.get("slug", "")
                    state = msg.get("state", {})
                    source = msg.get("source", "ws")
                    for e in entities.values():
                        if e.get("slug") == slug:
                            e["state"].update(state)
                            broadcast = json.dumps({
                                "type": "state_changed",
                                "entity_id": e["id"],
                                "entity_slug": slug,
                                "current_state": e["state"],
                                "changed_keys": list(state.keys()),
                                "source": source,
                                "timestamp": time.time()
                            })
                            for ws in ws_connections[:]:
                                if ws != websocket:
                                    try:
                                        await ws.send_text(broadcast)
                                    except:
                                        ws_connections.remove(ws)
            except:
                pass
    except WebSocketDisconnect:
        if websocket in ws_connections:
            ws_connections.remove(websocket)

# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {"status": "ok", "entities": len(entities), "connections": len(ws_connections)}

@app.get("/dashboard")
async def dashboard():
    html_path = os.path.join(os.path.dirname(__file__), "maestra-dashboard.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/")
async def root():
    return HTMLResponse("<h1>Maestra Fleet Manager</h1><p><a href='/dashboard'>Fleet Dashboard</a> | <a href='/audio'>Audio Analysis</a> | <a href='/health'>Health</a></p>")

@app.get("/audio", response_class=HTMLResponse)
async def audio_page():
    html_path = os.path.join(os.path.dirname(__file__), "audio-analysis.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
