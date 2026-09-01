# Context

## Glossary

### Starter VisWindow Layout Convention

The required layout and code-annotation convention that every starter demo must follow so developers can read the demo and directly use it as a template for a real algorithm integration.

It includes four required page regions: a title row, an input column, a render column, and a debug row.

It requires every starter demo to provide an example selector together with a paired example preview, except where the editable primary input already serves as the direct preview of the selected example.

It requires the Visualization Result area to use a square display region, where the configured height matches the rendered width so the result always occupies a substantial half-column visual area.

For structured text inputs such as JSON, the selector may be a dropdown. When the selected example is loaded directly into the editable primary input and that editor visibly presents the example content itself, that editor may serve as the example preview.

For visual inputs such as images and maps, the selector must be a gallery or thumbnail-based chooser paired with a visual preview.

In `PathPlannerDemo`, a map is a data resource rather than an image resource. The selected map payload remains the underlying map data, while the UI must provide a visual preview so users can inspect the selected environment before sending the request.

Upload inputs are supplemental entry points and must not replace the example selector or the example preview.

In demos that support uploads, the built-in example selection workflow must remain persistently visible in the input column. Upload is a parallel override path, not a replacement for the example-driven starter workflow.

Each starter demo `build()` method must use a fixed segmented comment skeleton so developers can immediately understand and copy the structure.

That comment skeleton must cover at least the title row, input column, render column, debug row, callback definitions, and event binding plus returned components.

This convention is a documentation and readability constraint on the existing code flow, not a requirement to extract each section into separate helper methods.

### Map Cell Picker

The PathPlannerDemo interaction concept that converts a user-selected map location into a grid cell coordinate. It is based on the current map data resource, not the rendered preview image, and synchronizes with the explicit start and goal coordinate controls.

### MapPreviewPointPicker

A reusable project-local component concept for map-based point selection. It displays a map preview, converts user clicks into grid cell selections against the underlying map data, and reports the selected cell together with its obstacle status without exposing its internal interaction mechanism to consuming VisWindow code.

Its first-stage implementation lives under `components/widgets/` as a project-local reusable UI building block rather than a separately packaged Gradio custom component.

It emits raw selection events in the form `mouse_button + cell_x + cell_y + is_obstacle`, rather than directly encoding `start` or `goal` semantics.

It is currently not wired into the starter `PathPlannerDemoVisWindow`, because the browser-level left/right click behavior proved unreliable enough to hurt template usability.

The current `PathPlannerDemoVisWindow` instead keeps map preview as plain `gr.Image` output and reports obstacle-state feedback through the `Start X/Y` and `Goal X/Y` slider labels.

## Mock Server Debug Output

Every mock server saves its latest rendered image to a fixed local `render.png` beside the corresponding `mock_server.py`.

Each new `/render` call overwrites the previous `render.png`, because mock servers are treated as single-step local debugging helpers rather than history-preserving services.
