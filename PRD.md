# PRD: Algorithm Visualization Platform

## Problem Statement

Algorithm developers already maintain separate Flask-based services for target perception, path planning, task allocation, and similar algorithms. Each service can run independently, but there is no shared visualization platform that lets users access a browser page, select an algorithm visualization, configure inputs, call the algorithm service, and view the returned visualization result.

The platform needs to make algorithm visualization easy to integrate without forcing every algorithm developer to build a complete web application. At the same time, each algorithm type has different input controls and visualization needs, so the platform must avoid an overly rigid metadata-driven UI schema that cannot express page-specific interaction patterns.

The first version should prioritize fast integration, clear boundaries, and reusable visualization components.

## Solution

Build a Gradio-based visualization platform server. Users access the platform through `ip:port` in a browser. The platform renders reusable visualization windows, each of which is an embeddable Gradio component bound to one external Flask algorithm server.

The visualization platform does not start or manage algorithm server processes. It only calls already-running algorithm services through a standard `/health` endpoint and a synchronous `/render` endpoint.

Each algorithm developer can implement a custom `VisWindow` in the platform repository. A `VisWindow` owns its own Gradio input controls, layout inside its local container, request packaging logic, and visualization result area. The top-level platform application manually places these windows into tabs, rows, columns, or other Gradio containers.

The first version provides three starter visualization windows:

1. `perception_demo`: image gallery/upload, IoU threshold, confidence threshold, class/conf checkboxes, image output.
2. `path_planner_demo`: map gallery/upload, start/goal coordinate sliders, inflation radius, path visualization checkboxes, image output.
3. `json_demo`: JSON input object, cost checkbox, image output.

All render requests use a stable outer request contract:

```json
{
  "input": {},
  "visualization": {},
  "request_id": "optional-client-generated-id"
}
```

All successful render responses return an image payload:

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

## User Stories

1. As an algorithm user, I want to open the visualization platform from a browser using an IP address and port, so that I can access algorithm demos without installing local UI tools.
2. As an algorithm user, I want to choose between different visualization windows, so that I can inspect perception, path planning, or JSON-driven algorithms from one platform.
3. As an algorithm user, I want to see whether an algorithm server is online, so that I know whether a visualization request is likely to work.
4. As an algorithm user, I want to refresh the health status of an algorithm server manually, so that I can re-check service availability after starting or restarting a server.
5. As an algorithm user, I want to use predefined input resources, so that I can quickly run a demo without manually constructing a request.
6. As an algorithm user, I want to upload my own image input, so that I can test perception algorithms on custom data.
7. As an algorithm user, I want to upload my own map data, so that I can test path planning algorithms on custom environments.
8. As an algorithm user, I want to adjust numeric parameters with sliders or input controls, so that I can quickly explore how parameters affect visualization results.
9. As an algorithm user, I want to toggle visualization options with checkboxes, so that I can control which overlays appear in the returned image.
10. As an algorithm user, I want to send a single render request and receive one visualization image, so that the interaction remains simple.
11. As an algorithm user, I want errors to be displayed clearly in the UI, so that I can understand whether the failure came from invalid input, service timeout, or server error.
12. As an algorithm user, I want to preview the full request JSON before sending it, so that I can verify exactly what will be sent to the algorithm server.
13. As an algorithm user, I want to copy the full request JSON, so that I can reproduce or debug a request outside the platform.
14. As an algorithm user, I want large binary fields to be summarized in the preview, so that the displayed request remains readable.
15. As a perception algorithm developer, I want a starter visualization window with image gallery, upload, thresholds, and checkbox overlays, so that I can integrate a detection-style service quickly.
16. As a path planning algorithm developer, I want a starter visualization window with map selection, start/goal coordinates, and path overlay controls, so that I can integrate a planner service quickly.
17. As a JSON-driven algorithm developer, I want a starter visualization window with a JSON editor and image result, so that I can integrate algorithms that accept arbitrary structured input.
18. As an algorithm developer, I want to implement my own visualization window in the platform repository, so that I can control UI components and layout for my algorithm.
19. As an algorithm developer, I want my visualization window to be embeddable, so that platform maintainers can place it in any tab or layout region.
20. As an algorithm developer, I want the platform context to provide server clients and resource helpers, so that my visualization window does not need to read config files or call raw URLs directly.
21. As an algorithm developer, I want a standard request envelope with `input`, `visualization`, and `request_id`, so that request structure is predictable across algorithms.
22. As an algorithm developer, I want the platform to support image payloads as base64 data, so that algorithm servers can run on different machines from the visualization platform.
23. As an algorithm developer, I want array/list and array/npy payload formats, so that map data can be reconstructed as NumPy arrays by the algorithm server.
24. As an algorithm developer, I want map coordinates to use `[x, y]`, so that UI coordinates match common horizontal/vertical expectations.
25. As an algorithm developer, I want map shape semantics to be fixed as `[H, W]` or `[H, W, C]`, so that slider ranges and server parsing are unambiguous.
26. As an algorithm developer, I want `array[y, x]` indexing documented, so that server-side map interpretation is consistent with UI coordinate selection.
27. As a platform maintainer, I want runtime configuration to contain only app launch settings and server endpoints, so that deployment changes do not require code edits.
28. As a platform maintainer, I want page layout to be defined in application code, so that custom layouts can be created without inventing a configuration DSL.
29. As a platform maintainer, I want each visualization window to bind to one algorithm server, so that integration remains simple and avoids hidden service chains.
30. As a platform maintainer, I want to place multiple visualization windows in one tab when needed, so that comparison or grouped demos can be created through layout code.
31. As a platform maintainer, I want reusable starter windows, so that new algorithm integrations can copy and adapt proven component patterns.
32. As a platform maintainer, I want resource manifests for galleries, so that preview files and actual request data files are explicitly linked.
33. As a platform maintainer, I want request and health calls to go through platform clients, so that timeouts, errors, and decoding are handled consistently.
34. As a platform maintainer, I want the render client to decode returned base64 images into displayable image objects, so that visualization windows do not duplicate decoding logic.
35. As a platform maintainer, I want no persistent request history in the first version, so that the platform avoids unnecessary storage, privacy, and cleanup concerns.
36. As a deployment operator, I want to change server IP addresses and ports in configuration, so that the platform can be moved between machines or networks easily.
37. As a deployment operator, I want per-server timeout settings, so that slow or unreachable algorithm servers do not block the UI indefinitely.
38. As a future contributor, I want a thin `BaseVisWindow` contract, so that I can understand the minimum required interface for adding a visualization window.
39. As a future contributor, I want utility modules separated by responsibility, so that configuration, HTTP, image, array, and resource logic do not become a single unmaintainable helper file.
40. As a future contributor, I want the first version to use `requirements.txt`, so that dependency installation is simple for a lightweight demo platform.

## Implementation Decisions

- The first version will use Gradio as the visualization platform framework instead of building a custom frontend/backend stack.
- The platform will run as a server and expose a browser-accessible UI through configured host and port.
- Algorithm services are external Flask servers and are not started, stopped, or supervised by the platform.
- Each algorithm service must expose `GET /health` and `POST /render`.
- `/health` is used only for service availability display.
- `/render` is a synchronous call that receives a full request payload and returns a rendered image.
- The platform will not split algorithm execution and visualization into separate `/run` and `/render` calls.
- Each visualization unit is called a `VisWindow`, not a page, because it is an embeddable component rather than a full page.
- `VisWindow` implementations must not create top-level Gradio application containers or top-level tabs.
- The top-level application file is responsible for manually placing visualization windows into tabs and layout regions.
- No registry is required in the first version. Manual layout in the application entry point is preferred.
- A thin `BaseVisWindow` abstraction will define only `window_id`, `title`, `server_key`, and `build(ctx)`.
- `window_id`, `title`, and `server_key` are passed during instantiation to support reuse of the same window class with different services.
- Each `VisWindow` binds to exactly one algorithm server in the first version.
- Runtime configuration contains only platform launch settings and algorithm server endpoint settings.
- Runtime configuration does not define component layout, component behavior, default parameters, checkbox labels, slider ranges, or resource lists.
- The application context passed to visualization windows provides loaded config, HTTP/render client, health client, and resource helpers.
- Visualization windows should not read configuration files directly.
- Visualization windows should not call raw algorithm server URLs directly.
- Render request payloads use the outer shape `input`, `visualization`, and optional `request_id`.
- Render success responses use the outer shape `status`, `image`, and optional `meta`.
- Render error responses use `status=error` and an `error` object with at least a readable message.
- Returned render images use base64-encoded image data.
- The platform render client decodes returned base64 images before passing them to Gradio output components.
- Supported payload content types in the first version are `image/png`, `image/jpeg`, `array/list`, and `array/npy`.
- `image/png` and `image/jpeg` payload `data` values are base64-encoded file bytes.
- `array/list` payload `data` values are JSON lists and are not base64-encoded.
- `array/npy` payload `data` values are base64-encoded `.npy` file bytes.
- `filename` may be included for display, logging, and debugging, but must not be interpreted as a server-local path.
- Map arrays use shape `[H, W]` or `[H, W, C]`.
- Map point coordinates use `[x, y]`, where `x` is horizontal/column and `y` is vertical/row.
- Server-side array indexing for map points is documented as `array[y, x]`.
- The path planner starter uses coordinate sliders in the first version instead of click-on-map coordinate selection.
- Path planner coordinate slider ranges are derived from selected or uploaded map shape.
- Starter resource directories are named `resources`, not `examples`.
- Gallery-like resources use a `manifest.json` that links display preview files to actual request data files.
- The first starter windows are `perception_demo`, `path_planner_demo`, and `json_demo`.
- Each starter includes a status/error output.
- Each starter includes a request JSON preview workflow.
- Request JSON preview uses both a summarized structured preview and a full copyable JSON text representation.
- The first version does not persist request history.
- Utility modules should be separated by responsibility rather than placing all helpers in one generic utility module.
- The first version uses `requirements.txt` for dependency management.

## Testing Decisions

- Tests should focus on externally visible behavior and integration seams, not internal Gradio layout implementation details.
- The highest-value seam is request packaging: given UI-equivalent inputs, the produced `/render` payload should match the documented protocol.
- The second highest-value seam is client behavior: given mocked algorithm server responses, the platform should correctly handle success, timeout, connection failure, invalid JSON, `status=error`, and invalid image payloads.
- Resource handling should be tested at the manifest-loading and payload-packing seam, ensuring preview/data/content_type fields produce the expected packaged resource payload.
- Map coordinate handling should be tested by selecting map shapes and verifying slider bounds and `[x, y]` request values.
- Image utilities should be tested by round-tripping image file bytes through base64 packaging and decoding.
- Array utilities should be tested for `array/list` and `array/npy` packaging semantics.
- Config loading should be tested by loading a representative runtime configuration and resolving server keys to endpoint settings.
- Health client behavior should be tested against mocked online, offline, timeout, and malformed health responses.
- Render client behavior should be tested against mocked successful image responses and error responses.
- Starter visualization windows should have lightweight smoke tests that instantiate and build inside a Gradio container where feasible.
- Full browser/UI automation is out of scope for the first version unless later regressions justify it.
- No existing test seams are present in the repository yet because the repository currently only contains planning documentation.
- New tests should be introduced around utility modules and clients first, because they are easier to validate deterministically than Gradio UI rendering.

## Out of Scope

- Starting, stopping, restarting, or supervising algorithm server processes.
- Managing algorithm server logs or lifecycle.
- Dynamic loading of frontend code from algorithm servers.
- Algorithm servers injecting arbitrary JavaScript or full frontend pages into the platform.
- A metadata-driven UI schema that attempts to describe every possible visualization page.
- A custom React/Vue frontend for the first version.
- Browser-to-algorithm-server direct requests.
- Asynchronous render jobs, task polling, cancellation, or result caching.
- Persistent request history.
- User authentication and authorization.
- Multi-user session management.
- Database storage.
- Automatic global health polling.
- Click-on-map point selection in the first version.
- One visualization window calling multiple algorithm servers.
- Runtime configuration of component layout or behavior.
- Automatic component discovery or registry-based layout.
- Publishing algorithm result files to persistent storage.
- Supporting non-image render outputs such as HTML, SVG, video, or interactive charts in the first version.

## Further Notes

- The platform should be intentionally simple in the first version because the main risk is over-designing a generic visualization DSL.
- The agreed design gives algorithm developers control over their own visualization components while preserving platform-level consistency for service calls, resources, request previews, and error handling.
- The top-level application can be replaced or duplicated later to create different layouts without modifying individual visualization windows.
- If future algorithms require long-running jobs, an async render protocol can be introduced for those windows without changing the first version's synchronous baseline.
- If future visualization outputs need to be interactive, they should be introduced through explicit supported render types and sandboxing rules rather than arbitrary server-injected frontend code.
- The current repository is not a Git repository and has no issue tracker connection available, so this PRD is captured locally instead of being published as an issue.

