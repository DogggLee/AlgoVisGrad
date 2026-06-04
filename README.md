# Algorithm Visualization Platform

Gradio-based visualization platform for external Flask algorithm services.

The current minimum demo is `JsonDemoVisWindow`. It loads a selectable JSON example, lets the user edit the JSON, calls an external mock Flask server, and displays the rendered image plus request/response JSON.

## Setup

Use the prepared conda environment:

```bash
conda activate algo_vis
```

If dependencies need to be installed from scratch:

```bash
pip install -r requirements.txt
```

## Run The JSON Demo

Start the mock algorithm server in one terminal:

```bash
conda activate algo_vis
python -m components.json_demo.mock_server
```

Start the Gradio visualization platform in another terminal:

```bash
conda activate algo_vis
python app.py
```

Open the Gradio URL printed by `app.py`.

The default config binds `json_demo` to:

```text
http://127.0.0.1:5003
```

## Run All Three Mock Demos

Start all three mock algorithm servers in one terminal:

```bash
conda activate algo_vis
./start_mock_demo.sh
```

This starts:

```text
perception_demo   http://127.0.0.1:5001
path_planner_demo http://127.0.0.1:5002
json_demo         http://127.0.0.1:5003
```

## Run The Map Drawer

Start the standalone local desktop map drawing tool:

```bash
conda activate algo_vis
python map_drawer.py
```

The tool opens a local window for drawing binary occupancy maps. Free cells use value `0` and painted obstacle cells use value `1`. Large maps remain fully accessible through the scrollable canvas. Left-drag paints obstacles, right-drag erases them, `Clear Obstacles` resets the current drawing, and the mouse wheel zooms the display without changing the underlying grid. You can also add a full obstacle border or randomly sample obstacle cells using one obstacle-ratio parameter before saving as either `json` or `npy`.

## JSON Demo Input

The selected JSON example has this shape:

```json
{
  "group1": [[20, 20], [60, 30]],
  "group2": [[140, 40], [110, 100]],
  "map_size": [160, 220]
}
```

`map_size` uses `[H, W]`.

Point coordinates use `[x, y]`.


## VisWindow Developer Workflow

A visualization unit is implemented as a `BaseVisWindow` subclass. It is an embeddable Gradio component, not a full page.

Minimum contract:

```python
class MyVisWindow(BaseVisWindow):
    def build(ctx):
        ...
```

Use `build(ctx)` to create controls inside the current Gradio container. Do not create `gr.Blocks` or top-level `gr.Tab` inside a `VisWindow`; the app layout owns those containers.

Use the application context instead of reading config files or calling raw URLs directly:

```python
ctx.render_client.render_image_response(server_key, payload)
ctx.health_client.check(server_key)
ctx.component_resource_path("json_demo")
```

Current JSON demo layout convention:

- Input column: example selector, preview/send controls, editable JSON input.
- Render column: service status near the title, visualization toggles, output image, status/error text.
- Debug row: full-width `Request JSON` and `Response JSON` tabs.

## Algorithm Server Contract

Health check:

```http
GET /health
```

Render request:

```http
POST /render
```

Request shape:

```json
{
  "input": {},
  "visualization": {},
  "request_id": "optional"
}
```

Successful image response:

```json
{
  "status": "success",
  "image": {
    "content_type": "image/png",
    "data": "base64..."
  },
  "meta": {}
}
```


Error response:

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "human-readable error"
  },
  "meta": {}
}
```

## Payload Content Types

Supported first-version payload content types:

```text
image/png
image/jpeg
array/list
array/npy
```

Semantics:

- `image/png`: `data` is PNG file bytes encoded as base64.
- `image/jpeg`: `data` is JPEG file bytes encoded as base64.
- `array/list`: `data` is a JSON list and is not base64 encoded.
- `array/npy`: `data` is `.npy` file bytes encoded as base64.

## Map And Coordinate Convention

Map array shapes use `[H, W]` or `[H, W, C]`.

Point coordinates use `[x, y]`.

- `x` is the horizontal coordinate and maps to the array column index.
- `y` is the vertical coordinate and maps to the array row index.

Server-side array indexing should use:

```python
value = array[y, x]
```

## Tests

Run the test suite:

```bash
conda activate algo_vis
python -m pytest -q
```
