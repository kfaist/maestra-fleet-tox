# Setup Guide

## Two Ways to Use Maestra Fleet

### Option A: Join the Demo Fleet (Recommended for Cohort)

Plug directly into Krista's live Maestra server. No deployment needed.

1. Drop `touchdesigner/maestra_fleet.tox` into your TD project
   (or run `build_tox.py` in the Textport to create one from scratch)

2. Set custom parameters on the TOX:
   - **Entity ID**: Pick a unique name like `yourname-scope` or `yourname-sd`
   - **Server URL**: `https://maestra-dashboard-production.up.railway.app`
   - **API Key**: (leave blank for now)

3. Click **Connect**

4. Your device shows up in the fleet dashboard
   - Krista can see your video output
   - You receive shared NLP prompts (P5/P6) from the speech pipeline
   - Your audio/visual parameters sync with all connected devices

5. To disconnect, click **Disconnect** or close TD. Your slot goes offline.

### Option B: Run Your Own Fleet

Deploy your own Maestra server for full control.

1. Install Railway CLI: `npm install -g @railway/cli`

2. Deploy the server:

```bash
cd server/
railway login
railway init
railway up
```

3. Note your Railway URL (e.g., `https://your-project-production.up.railway.app`)

4. Download the spaCy model (runs automatically on Railway via railway.toml):
```bash
python -m spacy download en_core_web_sm
```

5. Drop `maestra_fleet.tox` into your TD project

6. Set custom parameters:
   - **Entity ID**: Your device name
   - **Server URL**: Your Railway URL
   - Click **Connect**

## Connecting Video

### Video IN (browser webcam to TD)

The TOX automatically pulls webcam frames from the server. The browser
page at your server URL captures the webcam and POSTs frames to
`/video/frame/browser`. The TOX fetches these at ~12fps using threaded
urllib and decodes them with cv2 inside a Script TOP's cook() method.

Wire the TOX output to your pipeline:
```python
op('/project1/maestra_fleet').outputConnectors[0].connect(op('/project1/your_input'))
```

### Video OUT (TD output to browser)

Set the **Video Output TOP** parameter to the path of the TOP you want
to send back to the browser. For example:
```
/project1/flip1
```

The TOX captures that TOP, JPEG-encodes it with cv2 in a background
thread, and POSTs it to `/video/frame/td` on the server.

### Viewing Video in the Browser

Navigate to your server URL. The fleet dashboard shows connected devices
and their video output. Click a device slot to see its live feed.

## Connecting to StreamDiffusion

Wire the webcam feed into StreamDiffusion's input:
```python
op('/project1/maestra_fleet').outputConnectors[0].connect(op('/project1/StreamDiffusionTD'))
```

Set the Video Output TOP to StreamDiffusion's output:
```
/project1/StreamDiffusionTD/out1
```

Now the browser webcam feeds SD, and SD's output goes back to the browser.

## Connecting to Daydream Scope

Scope runs on a separate machine. Drop a second `maestra_fleet.tox`
into a minimal TD project on that machine:

1. Set Entity ID to something like `scope-background`
2. Set Server URL to the same Maestra server
3. Connect

Scope receives the same NLP prompts (P5) as your main TD instance.
Use those prompts to drive Scope's generation. Send Scope's output
back via the Video Output TOP parameter.

On the main TD machine, pull Scope's video from the server
(`/video/frame/scope`) and composite it as a background layer.
