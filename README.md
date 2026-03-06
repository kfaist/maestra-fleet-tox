# Maestra Fleet TOX

**Real-time fleet management for interactive installations using TouchDesigner, Daydream Scope, and more.**

Built by [Krista Faist](https://kristafaist.com) for the Daydream Cohort 3 and Currents x Relay: Ambient Intelligence exhibition.

## What is this?

A drop-in TouchDesigner component (.tox) that connects your TD project to a shared Maestra fleet manager server. Multiple devices (TD instances, Scope sessions, web browsers) can share state, video, and audio data in real-time over the internet.

**Use cases:**
- Multi-screen installations where several computers generate different layers
- Remote collaboration where artists in different locations combine outputs
- Live VJ setups with centralized prompt/parameter control
- Interactive installations where audience input drives multiple renderers

## Architecture

```
Browser (webcam + speech)
    |
    v
Maestra Server (Railway)  <-- Central hub
    |         |         |
    v         v         v
TD/SD      Scope     Other
Instance   Instance   Devices
(Krista1)  (Background) (Empty slots)
```

## Quick Start

### Option A: Join the Daydream Cohort Demo Fleet (Easiest)

No deployment needed. Plug directly into the live fleet:

1. Drop `touchdesigner/maestra_fleet.tox` into your TD project
2. Set **Server URL** to: `https://maestra-dashboard-production.up.railway.app`
3. Set **Entity ID** to something unique (e.g., `yourname-scope`)
4. Click **Connect** -- you're in the fleet

You'll receive shared NLP prompts, can send/receive video, and show up in the fleet dashboard. See `docs/SETUP.md` for details.

### Option B: Deploy Your Own Server

### 1. Deploy the Maestra Server

```bash
cd server/
railway up
```

Or deploy to any hosting that supports Python/FastAPI. The server handles:
- Entity registration and state sync
- Video frame relay (JPEG over HTTP)
- WebSocket real-time updates
- NLP transcript processing (spaCy)

### 2. Drop the TOX into TouchDesigner

1. Open your TD project
2. Drag `touchdesigner/maestra_fleet.tox` into your network
3. Set the custom parameters:
   - **Entity ID**: Your unique device name (e.g., `krista-sd`, `scope-bg`)
   - **Server URL**: Your Railway deployment URL
4. Click **Connect**

### 3. Wire Your Pipeline

The TOX exposes:
- **Output connector**: Live webcam feed from the browser (accessible outside the COMP)
- **send_frames**: Captures any TOP and POSTs it to the server for browser display

To connect webcam to your pipeline:
```python
# In TD, connect the TOX output to your input
op('/project1/maestra_fleet').outputConnectors[0].connect(op('/project1/your_input'))
```

To send your processed output back to the browser:
```python
# Edit send_frames Execute DAT to capture your output TOP
sd_out = op('/project1/your_output_top')
```

## For Cohort Members

### Joining the Fleet

1. Clone this repo
2. Drop `maestra_fleet.tox` into your TD project
3. Set your **Entity ID** to something unique (e.g., `yourname-scope`, `yourname-sd`)
4. Set **Server URL** to the shared Maestra server
5. Connect -- your device shows up in the fleet dashboard

### Your Device Slot

Each cohort member gets a slot in the fleet manager dashboard. When your device is connected:
- Your slot shows a green status indicator
- If you have video output, it appears in the preview window
- Your NLP prompts (P5/P6) are shared with all connected devices
- Your audio analysis data is available to other devices

### Removing Your Device

Disconnect from TD (click Disconnect) or just close your project. Your slot goes to "offline" status. No data persists after disconnection.

## Key Technical Details

### Video Pipeline (cv2 + numpy, no PIL needed)

The TOX uses OpenCV (cv2) for all JPEG encoding/decoding. This is available in TD 2023+ by default.

**Video IN (browser webcam to TD):**
- Execute DAT fetches JPEG frames via threaded urllib (non-blocking)
- Script TOP decodes with cv2.imdecode() inside its cook() method
- copyNumpyArray() renders the frame (only legal inside cook())

**Video OUT (TD output to browser):**
- Execute DAT captures a TOP with numpyArray(delayed=True)
- cv2.imencode() encodes to JPEG in a background thread
- Threaded POST to the server's /video/frame/td endpoint

### State Sync

All devices share state through the Maestra entity system:
- P5 (noun phrase from speech) drives prompts across all devices
- Audio levels, visual parameters, and custom state are synced via WebSocket
- HTTP polling fallback for reliability

### Known Issues

- TD's Web Client DAT returns `statusCode` as a dict `{'code': 200}`, not an int
- `copyNumpyArray()` can ONLY be called inside a Script TOP's cook() method
- `time.sleep()` blocks TD's main thread and prevents async callbacks from firing
- The Execute DAT's `onFrameStart` with `cam.cook(force=True)` is required to keep the Script TOP cooking

## File Structure

```
maestra-fleet-tox/
â”œâ”€â”€ README.md
â”œâ”€â”€ touchdesigner/
â”‚   â”œâ”€â”€ maestra_fleet.tox          # The main TOX (drop into any TD project)
â”‚   â””â”€â”€ build_tox.py               # Script to rebuild the TOX from scratch
â”œâ”€â”€ server/
â”‚   â”œâ”€â”€ server.py                  # FastAPI Maestra server
â”‚   â”œâ”€â”€ requirements.txt           # Python dependencies
â”‚   â”œâ”€â”€ Procfile                   # Railway deployment
â”‚   â””â”€â”€ railway.toml               # Railway config
â””â”€â”€ docs/
    â”œâ”€â”€ SETUP.md                   # Detailed setup guide
    â”œâ”€â”€ TROUBLESHOOTING.md         # Common issues and fixes
    â””â”€â”€ FLEET_DASHBOARD.md         # Fleet manager dashboard docs
```

## Password Protection

The TOX can be password-protected in TouchDesigner:
1. Right-click the COMP
2. Properties > set a password
3. This locks the internals -- others can use inputs/outputs but can't see the code

## License

- **Maestra framework** (Jordan Snyder / Meow Wolf) â€” MIT
- **This TOX & fleet manager** (Krista Faist) â€” [AGPL 3.0](https://www.gnu.org/licenses/agpl-3.0.html)

AGPL 3.0 means you can use, modify, and distribute freely â€” but any modified version you deploy as a network service must also be open source under AGPL. For commercial use without that requirement, dual-licensing is available â€” contact krista@krista.art.

## Credits

- **Krista Faist** â€” TOX development, fleet architecture, fleet manager dashboard
- **Jordan Snyder / Meow Wolf** â€” Maestra framework (MIT)
- **Daydream / Livepeer** â€” Scope, StreamDiffusion ecosystem
- **DotSimulate** â€” StreamDiffusionTD component

