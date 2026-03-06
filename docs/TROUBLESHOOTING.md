# Troubleshooting

## Common Issues

### Webcam freezes in TD

The most common issue. Check these in order:

1. **frame_update Execute DAT not active**
   In Textport:
   ```
   op('/project1/maestra_fleet/frame_update').par.active = False
   op('/project1/maestra_fleet/frame_update').par.active = True
   ```

2. **script_cam_callbacks _last_id is stale**
   Reset it:
   ```
   op('/project1/maestra_fleet/script_cam_callbacks').module._last_id = -1
   ```

3. **Browser stopped sending frames**
   Check: `curl https://YOUR_SERVER/video/status`
   If `browser: false`, reload the browser page.

### Nvidia Background Removal shows checkered pattern

The input resolution is too small. Nvidia requires at least 288px height.
```
op('/project1/maestra_fleet/script_cam').par.resolutionw = 1280
op('/project1/maestra_fleet/script_cam').par.resolutionh = 720
```

### cam_out shows 128x128 instead of full resolution

The Null TOP lost its connection to script_cam:
```
op('/project1/maestra_fleet/script_cam').outputConnectors[0].connect(
    op('/project1/maestra_fleet/cam_out'))
```

### StreamDiffusion shows banana/default instead of webcam

The webcam isn't connected to SD's input. Wire it:
```
op('/project1/maestra_fleet').outputConnectors[0].connect(
    op('/project1/StreamDiffusionTD'))
```

## TD-Specific Gotchas

### statusCode is a dict, not an int

TD's Web Client DAT returns `statusCode` as `{'code': 200, 'message': 'OK'}`.
Always extract the code:
```python
code = statusCode.get('code', 0) if isinstance(statusCode, dict) else statusCode
```

### copyNumpyArray only works inside cook()

`scriptOP.copyNumpyArray()` can ONLY be called from inside a Script TOP's
own `cook()` method. Calling it from an Execute DAT's `onFrameStart` or
any other context will throw:
```
td.tdError: Expected locked operator, or execution within onCook method
```

The workaround: use an Execute DAT to call `cam.cook(force=True)` on every
frame, which triggers the Script TOP's cook() where copyNumpyArray is legal.

### time.sleep() blocks TD

Never use `time.sleep()` in TD scripts. It blocks the main thread and
prevents async callbacks from firing. Use `run()` with `delayFrames`
for deferred execution, or threaded approaches for network requests.

### Web Client DAT clamp parameter

The `clamp` parameter on Web Client DAT must be set to `"none"` for
binary data (JPEG frames). If it's set to `"text"`, binary data gets
corrupted. This parameter can reset when the DAT is toggled.

### PIL/Pillow is NOT available in TD

Despite what the Textport might suggest, PIL is not reliably available
in TD 2023's Python environment. Use cv2 (OpenCV 4.8.0) and numpy
(1.24.1) instead, which ARE available by default.

## MCP Server Issues

### ModuleNotFoundError: No module named 'mcp'

The TouchDesigner MCP server lost its Python path. Fix it:
```
import sys
sys.path.insert(0, 'PATH_TO/touchdesigner-mcp-td/modules')
sys.path.insert(0, 'PATH_TO/touchdesigner-mcp-td/modules/td_server')
exec(open('PATH_TO/fix_mcp_full.py').read())
```

### OpenAPI schema not loading

The MCP webserver needs the YAML schema loaded manually after restart:
```python
import yaml, mcp
f = open('PATH_TO/openapi.yaml')
mcp.openapi_schema = yaml.safe_load(f)
f.close()
```
