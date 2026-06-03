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

## Tests

Run the test suite:

```bash
conda activate algo_vis
python -m pytest -q
```
