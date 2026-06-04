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
