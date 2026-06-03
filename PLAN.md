# Algorithm Visualization Platform Plan

## Goal

Build a lightweight visualization platform for existing algorithm services such as perception, path planning, and task allocation.

The platform runs as a server. Users access it from a browser through `ip:port`, select a visualization window, configure inputs, send one request to the corresponding algorithm service, and view the returned visualization image.

## Core Architecture

The first version uses Gradio as the visualization platform framework.

```text
Browser
  -> Gradio Visualization Platform
      -> external Flask Algorithm Server /health
      -> external Flask Algorithm Server /render
```

The visualization platform does not start, stop, or manage algorithm server processes. It only calls already-running algorithm servers.

Each algorithm server is an independent Flask service. The platform only assumes the server exposes:

```http
GET /health
POST /render
```

The platform is responsible for:

- Gradio UI layout.
- Algorithm service status display.
- Input component rendering.
- Request payload packaging.
- Calling `/render`.
- Decoding and displaying returned images.
- Showing request JSON preview and errors.

The algorithm server is responsible for:

- Parsing the request payload.
- Running the algorithm.
- Drawing the visualization.
- Returning the rendered image.

## Gradio Layout Model

The platform uses `app.py` to define the top-level Gradio layout manually.

`app.py` is responsible for:

- Creating `gr.Blocks`.
- Creating top-level `Tabs`, rows, columns, or other containers.
- Placing reusable visualization windows into those containers.
- Binding each visualization window to one configured algorithm server.

Visualization windows must be embeddable components. A visualization window must not create its own top-level `gr.Blocks` or top-level `gr.Tab`.

Example target usage:

```python
with gr.Blocks() as demo:
    with gr.Tabs():
        with gr.Tab("Perception"):
            PerceptionDemoVisWindow(
                window_id="perception_demo",
                title="Perception Demo",
                server_key="perception",
            ).build(ctx)

        with gr.Tab("Path Planner"):
            PathPlannerDemoVisWindow(
                window_id="path_planner_demo",
                title="Path Planner Demo",
                server_key="path_planner",
            ).build(ctx)
```

If a future layout needs multiple visualization windows in one tab, it can be handled directly in `app.py`:

```python
with gr.Tab("Comparison"):
    with gr.Row():
        with gr.Column():
            PathPlannerDemoVisWindow(..., server_key="astar").build(ctx)
        with gr.Column():
            PathPlannerDemoVisWindow(..., server_key="dwa").build(ctx)
```

## Visualization Window Model

Each algorithm UI unit is called a `VisWindow`.

The first version defines a thin `BaseVisWindow` abstraction. It only constrains:

- `window_id`
- `title`
- `server_key`
- `build(ctx)`

`window_id`, `title`, and `server_key` are passed during instantiation instead of being hard-coded as class-level constants. This allows the same `VisWindow` implementation to be reused with different algorithm services.

Example:

```python
@dataclass
class BaseVisWindow(ABC):
    window_id: str
    title: str
    server_key: str

    @abstractmethod
    def build(self, ctx) -> None:
        ...
```

Each `VisWindow` binds to exactly one algorithm server in the first version. There is no need to support one visualization window calling multiple algorithm servers.

## Runtime Configuration

Runtime configuration is intentionally thin.

`config.yaml` contains only:

- Platform launch config.
- Algorithm server endpoint config.

It does not contain:

- Component layout.
- Slider ranges.
- Checkbox names.
- Gallery file lists.
- Default algorithm parameters.
- Visualization behavior.

Those belong in `VisWindow` code and local component resources.

Target structure:

```yaml
app:
  host: 0.0.0.0
  port: 7860
  title: Algorithm Visualization Platform

servers:
  perception:
    base_url: http://127.0.0.1:5001
    health_path: /health
    render_path: /render
    timeout_seconds: 30

  path_planner:
    base_url: http://127.0.0.1:5002
    health_path: /health
    render_path: /render
    timeout_seconds: 30

  json_demo:
    base_url: http://127.0.0.1:5003
    health_path: /health
    render_path: /render
    timeout_seconds: 30
```

## App Context

`app.py` creates and passes an application context object into every `VisWindow`.

The first version of `ctx` should provide:

- `config`: loaded runtime configuration.
- `http_client`: render request client.
- `health_client`: health check client.
- Resource path helpers.

Visualization windows should not read the config file directly and should not call algorithm server URLs directly. They should use `ctx`.

## Algorithm Server Contract

### Health Check

Each algorithm server should provide:

```http
GET /health
```

Recommended response:

```json
{
  "status": "ok",
  "name": "path_planner",
  "version": "1.0.0"
}
```

The platform displays service state. First version behavior:

- Check once when the UI loads, where practical.
- Provide a manual refresh button.
- Do not implement global automatic polling.

Recommended displayed states:

- `online`
- `offline`
- `timeout`
- `error`
- `unknown`

### Render Request

Each algorithm server should provide:

```http
POST /render
```

The request body uses a stable outer protocol:

```json
{
  "input": {},
  "visualization": {},
  "request_id": "optional-client-generated-id"
}
```

The platform does not care whether the algorithm server internally separates algorithm execution and drawing. The platform only makes one synchronous `/render` request and expects one visualization result.

### Render Response

Successful response:

```json
{
  "status": "success",
  "image": {
    "content_type": "image/png",
    "data": "base64..."
  },
  "meta": {
    "elapsed_ms": 123
  }
}
```

Error response:

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "start point is outside map"
  },
  "meta": {}
}
```

The first version uses synchronous requests with per-server timeout configured in `config.yaml`.

## Supported Payload Content Types

The first version supports these payload `content_type` values:

```text
image/png
image/jpeg
array/list
array/npy
```

Semantics:

```text
image/png
  data is PNG file bytes encoded as base64.

image/jpeg
  data is JPEG file bytes encoded as base64.

array/list
  data is a JSON list. It is not base64 encoded.

array/npy
  data is .npy file bytes encoded as base64.
```

`filename` may be included for display, logging, and debugging. It must not be treated as a filesystem path by the algorithm server.

Recommended image payload:

```json
{
  "content_type": "image/png",
  "filename": "street_001.png",
  "data": "base64..."
}
```

Recommended array/list payload:

```json
{
  "content_type": "array/list",
  "filename": "warehouse_01.json",
  "shape": [100, 100, 3],
  "dtype": "uint8",
  "data": [[[0, 0, 0]]]
}
```

Recommended array/npy payload:

```json
{
  "content_type": "array/npy",
  "filename": "warehouse_01.npy",
  "shape": [100, 100, 3],
  "dtype": "uint8",
  "data": "base64..."
}
```

## Map Data and Coordinates

Map data should be recoverable as a NumPy array.

Supported map shapes:

```text
[H, W]
[H, W, C]
```

Coordinate convention:

```text
point = [x, y]
x = horizontal coordinate = column index = 0 to W - 1
y = vertical coordinate = row index = 0 to H - 1
```

Array indexing convention:

```python
value = array[y, x]
```

For `path_planner_demo`, the first version uses coordinate sliders instead of map click selection.

Slider behavior:

- `start_x` and `goal_x` maximum should be `W - 1`.
- `start_y` and `goal_y` maximum should be `H - 1`.
- Slider ranges should update after selecting or uploading a map.

Map click selection can be added later without changing the request protocol.

## Starter Visualization Windows

The first version provides three starter visualization windows.

### `perception_demo`

Input configuration group:

- Built-in image gallery.
- User image upload.
- IoU threshold slider or numeric input.
- Confidence threshold slider or numeric input.

Visualization result group:

- `class_id` checkbox.
- `conf` checkbox.
- Output image canvas.
- Status/error text.
- Request JSON preview/copy area.

Request shape:

```json
{
  "input": {
    "image": {
      "content_type": "image/jpeg",
      "filename": "street_001.jpg",
      "data": "base64..."
    },
    "iou_threshold": 0.5,
    "conf_threshold": 0.35
  },
  "visualization": {
    "show_class_id": true,
    "show_conf": true
  },
  "request_id": "..."
}
```

### `json_demo`

Input configuration group:

- JSON object editor.

Visualization result group:

- `cost` checkbox.
- Output image canvas.
- Status/error text.
- Request JSON preview/copy area.

Request shape:

```json
{
  "input": {
    "payload": {}
  },
  "visualization": {
    "show_cost": true
  },
  "request_id": "..."
}
```

### `path_planner_demo`

Input configuration group:

- Built-in map gallery.
- User map upload, supporting `.json` and `.npy`.
- Start coordinate sliders: `start_x`, `start_y`.
- Goal coordinate sliders: `goal_x`, `goal_y`.
- Inflation radius threshold slider or numeric input.

Visualization result group:

- `start` checkbox.
- `goal` checkbox.
- `path_cost` checkbox.
- `candidate_paths` checkbox.
- `inflation_area` checkbox.
- Output image canvas.
- Status/error text.
- Request JSON preview/copy area.

Request shape:

```json
{
  "input": {
    "map": {
      "content_type": "array/npy",
      "filename": "warehouse_01.npy",
      "shape": [100, 100, 3],
      "dtype": "uint8",
      "data": "base64..."
    },
    "start": [10, 20],
    "goal": [80, 60],
    "inflation_radius": 2
  },
  "visualization": {
    "show_start": true,
    "show_goal": true,
    "show_path_cost": true,
    "show_candidate_paths": false,
    "show_inflation_area": true
  },
  "request_id": "..."
}
```

## Resources

Each starter keeps local resources under its own component directory.

Use `resources`, not `examples`, to avoid confusion between sample data and code examples.

Target structure:

```text
components/
  perception_demo/
    vis_window.py
    resources/
      manifest.json
      images/

  path_planner_demo/
    vis_window.py
    resources/
      manifest.json
      maps/

  json_demo/
    vis_window.py
    resources/
      manifest.json
      inputs/
```

Gallery-like resources use `resources/manifest.json`.

Manifest item format:

```json
{
  "id": "warehouse_01",
  "name": "Warehouse 01",
  "preview": "maps/warehouse_01.png",
  "data": "maps/warehouse_01.npy",
  "content_type": "array/npy",
  "shape": [100, 100, 3],
  "dtype": "uint8"
}
```

For perception:

```json
{
  "id": "street_001",
  "name": "Street 001",
  "preview": "images/street_001.jpg",
  "data": "images/street_001.jpg",
  "content_type": "image/jpeg"
}
```

## Request JSON Preview

The first version does not persist request history.

Every starter should provide:

- A `Preview Request JSON` button.
- A `Send Render Request` button.
- A summary JSON preview.
- A full JSON textbox with copy support.

The summary preview should abbreviate large fields such as base64 image data:

```json
{
  "data": "<base64 length=238194>"
}
```

The full JSON textbox should contain the complete request payload for copying and reproduction.

Click behavior:

- `Preview Request JSON`: assemble payload and update summary/full JSON only.
- `Send Render Request`: assemble payload, update summary/full JSON, call `/render`, display image or error.

## Error Handling

Every starter should include a status/error text output.

The platform should normalize these failure modes:

- Config does not contain `server_key`.
- Health check connection failed.
- Health check timed out.
- Render request connection failed.
- Render request timed out.
- Algorithm server returned `status=error`.
- Algorithm server returned invalid JSON.
- Algorithm server returned invalid base64 image data.

Recommended render behavior:

- On success: display image and status text.
- On failure: clear image or leave previous image by explicit design, and display error text.

The first version can clear the image on failure for simpler behavior.

## Utility Modules

Use separate utility modules instead of putting everything in `utils.py`.

Suggested structure:

```text
utils/
  __init__.py
  utils.py
  config_utils.py
  http_utils.py
  image_utils.py
  array_utils.py
  resource_utils.py
```

Agreed direction:

- `utils.py` should stay small and only contain generic config/file IO helpers if needed.
- HTTP request logic should live in `http_utils.py` or a dedicated client module.
- Image/base64 conversion should live in `image_utils.py`.
- Array/list/npy packaging should live in `array_utils.py`.
- Manifest and resource path handling should live in `resource_utils.py`.

## Proposed Initial File Structure

```text
algo_vis/
  app.py
  config.yaml
  requirements.txt
  PLAN.md

  components/
    __init__.py
    base.py

    perception_demo/
      __init__.py
      vis_window.py
      resources/
        manifest.json
        images/

    path_planner_demo/
      __init__.py
      vis_window.py
      resources/
        manifest.json
        maps/

    json_demo/
      __init__.py
      vis_window.py
      resources/
        manifest.json
        inputs/

  utils/
    __init__.py
    utils.py
    config_utils.py
    http_utils.py
    image_utils.py
    array_utils.py
    resource_utils.py
```

## Dependencies

Use `requirements.txt` for the first version.

Expected dependencies:

```text
gradio
requests
pydantic
pyyaml
pillow
numpy
```

## First Implementation Milestones

1. Create `requirements.txt` and `config.yaml`.
2. Implement configuration loading.
3. Implement `BaseVisWindow`.
4. Implement app context.
5. Implement health client.
6. Implement render HTTP client.
7. Implement image/base64 utilities.
8. Implement array/list and array/npy payload packaging.
9. Implement manifest resource loading.
10. Implement `perception_demo` starter.
11. Implement `json_demo` starter.
12. Implement `path_planner_demo` starter.
13. Wire all starters manually in `app.py`.
14. Add minimal sample resources.
15. Add basic import/syntax verification.

