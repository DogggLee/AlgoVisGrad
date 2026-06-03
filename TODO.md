# TODO

## Done

- [x] Define platform plan in `PLAN.md`.
- [x] Define PRD in `PRD.md`.
- [x] Add `requirements.txt` dependency list.
- [x] Add `pytest.ini` test configuration.
- [x] Add default `config.yaml` with `app` and `servers` sections.
- [x] Implement config loading with `load_config(path) -> AppConfig`.
- [x] Implement `HealthClient.check(server_key)` online success path.
- [x] Implement `RenderClient.render_image(server_key, payload)` success path.
- [x] Implement resource packing for `image/png` and `image/jpeg`.
- [x] Implement resource packing for `array/list`.
- [x] Implement resource packing for `array/npy`.
- [x] Implement `load_manifest(resources_dir)`.
- [x] Implement payload summary helper for request JSON previews.
- [x] Restrict payload summary shortening to large `data` fields only.
- [x] Implement thin `BaseVisWindow` contract.
- [x] Implement `AppContext.component_resource_path(...)`.
- [x] Implement `create_app_context(config_path, project_root)`.
- [x] Implement `perception_demo` payload builder.
- [x] Implement `path_planner_demo` payload builder with `[x, y]` coordinates.
- [x] Implement `json_demo` payload builder.
- [x] Implement minimal `JsonDemoVisWindow` Gradio UI.
- [x] Implement JSON demo request preview helper.
- [x] Wire JSON demo preview button.
- [x] Add copy button to JSON demo full request textbox with `buttons=["copy"]`.
- [x] Implement JSON demo render handler success path.
- [x] Wire JSON demo render button.
- [x] Implement JSON demo mock Flask server for the minimum demo.
- [x] Validate JSON demo mock server payload and return standard error responses.
- [x] Add JSON demo example selector before loading input JSON.
- [x] Make JSON demo input directly editable with `gr.Code(language="json")`.
- [x] Move JSON demo Show Cost checkbox above Visualization Result.
- [x] Replace Full JSON textbox with Request JSON and Response JSON tabs.
- [x] Put JSON Example, Preview, and Send controls in one top row.
- [x] Align Show Cost control row with JSON Example row.
- [x] Set Visualization Result height to match Input JSON editor height.
- [x] Establish JSON demo layout convention: input column, render column, full-width debug row.
- [x] Add minimal `app.py` Gradio app builder.
- [x] Verify current implementation with `conda run -n algo_vis python -m pytest -q`.

## Next

- [x] Replace placeholder JSON tab in `app.py` with `JsonDemoVisWindow`.
- [x] Add error handling path for `run_json_demo_render(...)`.
- [x] Normalize render client errors into a platform exception.
- [x] Normalize health client timeout/offline/error states.
- [x] Add health status display and manual refresh button to `JsonDemoVisWindow`.
- [x] Move JsonDemo service status to title row as green/red dot with refresh button.
- [x] Replace HTML status indicator with Gradio Markdown/Button components.
- [x] Check JsonDemo server health once during initial window build.
- [x] Handle invalid editable JSON input in JsonDemo preview and render flows.
- [x] Add `PerceptionDemoVisWindow` minimal Gradio UI.
- [x] Add perception demo request preview helper.
- [ ] Wire perception demo preview and render buttons.
- [ ] Add `PathPlannerDemoVisWindow` minimal Gradio UI.
- [ ] Add path planner request preview helper.
- [ ] Wire path planner preview and render buttons.
- [ ] Add path planner coordinate sliders.
- [ ] Update path planner coordinate slider maximums from selected map shape.

## Resources

- [x] Create `components/perception_demo/resources/manifest.json`.
- [x] Add minimal perception demo image resources.
- [ ] Create `components/path_planner_demo/resources/manifest.json`.
- [ ] Add minimal path planner map resources.
- [x] Create `components/json_demo/resources/manifest.json`.
- [x] Add minimal JSON demo input resources if useful.

## Documentation

- [x] Add JSON demo mock server run instructions.
- [x] Add `README.md` with setup, run, and test commands.
- [x] Document algorithm server `/health` and `/render` contracts.
- [x] Document supported payload `content_type` values.
- [x] Document `VisWindow` developer workflow.
- [x] Document map shape and `[x, y]` coordinate conventions.

## Maintenance

- [x] Add `.gitignore` for Python cache, pytest cache, local env files, and generated outputs.
- [x] Move duplicated test HTTP server helpers into test utilities.
- [ ] Consider extracting shared request preview/render button patterns after all three demos exist.
- [ ] Consider adding lightweight app smoke test for each demo tab once real windows are wired.

## Backlog

- [ ] Support map click selection for start/goal coordinates.
- [ ] Support one tab containing multiple `VisWindow` instances for comparison layouts.
- [ ] Add richer request IDs.
- [ ] Add optional request/result download.
- [ ] Add async render workflow for slow algorithm services.
- [ ] Add non-image render types only if V1 image-only workflow becomes insufficient.

## Out Of Scope For V1

- [ ] Starting, stopping, or supervising algorithm server processes.
- [ ] Dynamic frontend code loading from algorithm servers.
- [ ] Arbitrary JavaScript or unsandboxed HTML returned by algorithm servers.
- [ ] Metadata-driven UI schema for all algorithms.
- [ ] Custom React/Vue frontend.
- [ ] Persistent request history.
- [ ] Authentication and authorization.
- [ ] Database storage.
- [ ] Automatic global health polling.
- [ ] One `VisWindow` calling multiple algorithm servers.
