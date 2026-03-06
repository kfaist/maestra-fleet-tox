# Setup Guide

**Maestra Fleet TOX** — TouchDesigner component for connecting to a Maestra fleet server.  
Built by Krista Faist on Jordan Snyder's Maestra framework (Meow Wolf, MIT).  
This TOX: AGPL 3.0 — dual-licensing available for commercial use.

---

## Prerequisites

- TouchDesigner 2023.11340 or later
- Python packages available by default in TD: `cv2` (OpenCV 4.8), `numpy`, `urllib`, `json`
- A running Maestra server (deploy your own or use an existing one)
- The `maestra_fleet.tox` file from `touchdesigner/` in this repo

---

## Quickstart: Drop and Connect

1. **Drop** `touchdesigner/maestra_fleet.tox` into your TD project network

2. **Open the component's custom parameters** (press `p` with the COMP selected)

3. **Set the Connection parameters:**
   - `Entity ID` — a unique name for this machine, e.g. `krista-main`, `scope-bg`, `audio-reactive`
   - `Server URL` — the base URL of your Maestra server, e.g. `https://your-project.up.railway.app`
   - `API Key` — leave blank unless your server requires one
   - `Auto Connect` — toggle on to connect automatically on project load

4. **Click Connect** (or pulse the Connect parameter)

5. Your device appears in the fleet dashboard. Done.

---

## Custom Parameters Reference

### Connection Page
| Parameter | Type | Description |
|-----------|------|-------------|
| Entity ID | String | Unique identifier for this machine on the fleet |
| Server URL | String | Base URL of your Maestra server (no trailing slash) |
| API Key | String | Optional — leave blank if server is open |
| Auto Connect | Toggle | Connect automatically when project loads |
| Connect | Pulse | Manually connect to server |
| Disconnect | Pulse | Disconnect from server |
| Status | String (read-only) | Current connection status |
| Heartbeat Interval | Int | Seconds between heartbeat pings (default: 5) |

### State Page
| Parameter | Type | Description |
|-----------|------|-------------|
| Brightness | Float 0–100 | Sent to server on change |
| Opacity | Float 0–1 | Sent to server on change |
| Color | RGB | Sent to server on change |
| Speed | Float 0–10 | Sent to server on change |
| Scene | Int | Scene index, sent to server on change |
| Custom State | String (JSON) | Arbitrary JSON pushed to server |
| Push State | Pulse | Manually push current state |
| Pull State | Pulse | Pull latest state from server |

### Streams Page
| Parameter | Type | Description |
|-----------|------|-------------|
| Stream Name | String | Human-readable name for this machine's output |
| Stream Type | Menu | NDI / Syphon / Spout / RTMP / SRT / WebRTC |
| Protocol | String | Protocol string passed to stream registry |
| Address | String | IP or hostname for stream |
| Port | Int | Port for stream |
| Advertise Stream | Pulse | Register this stream in the fleet registry |
| List Streams | Pulse | Pull available streams from registry into log |
| Active Stream ID | String (read-only) | ID returned by server after advertising |

### Gateways Page
| Parameter | Type | Description |
|-----------|------|-------------|
| OSC In Port | Int | Local OSC receive port |
| OSC Out Port | Int | OSC send port |
| OSC Prefix | String | OSC address prefix (default: `/maestra`) |
| WebSocket Enable | Toggle | Enable internal WS listener |
| WebSocket Port | Int | WS port |
| MQTT Enable | Toggle | Enable MQTT bridge |
| MQTT Broker | String | MQTT broker address |
| MQTT Port | Int | MQTT broker port |

---

## Video Pipeline

### Video OUT — TD output to server

Set the `Video Output TOP` parameter to the path of the TOP you want to send:
```
/project1/out1
```
The TOX captures that TOP, JPEG-encodes it with `cv2` in a background thread, and POSTs it to `/video/frame/td` on the server. This is visible in the fleet dashboard.

### Video IN — server/browser feed to TD

The TOX fetches frames from `/video/frame/browser` at ~12fps using threaded urllib. It decodes with `cv2.imdecode()` inside a Script TOP's `cook()` method. Wire the TOX output connector to your input:
```python
op('/project1/maestra_fleet').outputConnectors[0].connect(op('/project1/your_input'))
```

---

## Wiring to Scope (Daydream)

Scope runs locally on a single machine — it handles AI diffusion. The TOX handles fleet coordination. They're separate concerns:

1. Scope outputs via NDI. In TD, add an **NDI In TOP** pointing at Scope's output.
2. Feed that NDI In TOP into your pipeline.
3. Drop the Maestra TOX into the same TD project.
4. Use the TOX's state callbacks (via `par_exec`) to push prompt/scene changes to Scope via OSC:

```python
# In par_exec — fires when any state parameter changes
def onValueChange(par, prev):
    if par.name == 'Scene':
        scene = par.eval()
        prompts = {0: 'ethereal cave', 1: 'baroque gold', 2: 'cyberpunk rain'}
        op('scope_osc_out').sendOSC('/scope/prompt', prompts.get(scene, ''))
```

---

## Deploying Your Own Server

The server is a FastAPI Python app. Quickest path is Railway:

```bash
cd server/
railway login
railway init --name my-maestra
railway up
```

Railway auto-detects the `Procfile` and `requirements.txt`. Your server URL will be something like `https://my-maestra-production.up.railway.app`.

The `railway.toml` sets the root directory and build commands. The `Procfile` starts uvicorn on the Railway-assigned `$PORT`.

To run locally for development:
```bash
pip install -r requirements.txt
uvicorn server:app --reload --port 8080
```

---

## Using build_tox.py

If you want to rebuild the TOX from scratch (e.g. you've modified the internal scripts and want to regenerate):

1. Open TouchDesigner
2. Open the Textport (`alt+t`)
3. Run:
```python
exec(open('C:/path/to/maestra-fleet-tox/touchdesigner/build_tox.py').read())
```

The script reads `Server URL` from the custom parameter (so set that first), creates all internal operators, and saves a new `.tox` file.

---

## License

- **Maestra framework** — MIT (Jordan Snyder / Meow Wolf)
- **This TOX & fleet manager** — AGPL 3.0 (Krista Faist)

Commercial use without AGPL copyleft requirements: contact krista@krista.art
