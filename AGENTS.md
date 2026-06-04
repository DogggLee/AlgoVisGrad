# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python Gradio visualization platform for external Flask algorithm services.

- `app.py`: top-level Gradio app layout and launch entrypoint.
- `config.yaml`: runtime app/server endpoint configuration.
- `components/`: embeddable visualization windows.
- `components/base.py`: shared `BaseVisWindow` contract.
- `components/json_demo/`: implemented JSON demo window, resources, and mock Flask server.
- `components/perception_demo/`: perception demo window and image resources.
- `components/path_planner_demo/`: path planner payload code; UI work is still ongoing.
- `utils/`: config loading, app context, health/render clients, resource packing, payload preview helpers.
- `tests/`: pytest suite and test helpers.
- `PLAN.md`, `PRD.md`, `TODO.md`: planning, product scope, and implementation status.

## Build, Test, and Development Commands

Use the prepared conda environment:

```bash
conda activate algo_vis
```

Install dependencies if needed:

```bash
pip install -r requirements.txt
```

Run all tests:

```bash
python -m pytest -q
```

Run the JSON demo mock server:

```bash
python -m components.json_demo.mock_server
```

Run the Gradio platform:

```bash
python app.py
```

## Coding Style & Naming Conventions

Use Python 3.10+ with 4-space indentation and type hints for public functions. New public functions/classes should include concise docstrings describing purpose, arguments, and returns. Prefer explicit names such as `run_json_demo_render` and `preview_perception_request`. Visualization components should be named `*VisWindow` and should subclass `BaseVisWindow`.

Do not create top-level `gr.Blocks` or `gr.Tab` inside a `VisWindow`; `app.py` owns top-level layout.

注释要求：
- 每个函数头需写明功能、输入/输出参数（名称、类型、含义）。
- 函数内部关键步骤建议用简洁注释说明逻辑。

## Testing Guidelines

Tests use `pytest`. Add tests before implementation when changing behavior. Prefer public-interface tests over implementation-detail tests. Test files follow `tests/test_*.py`. Use `tests/helpers.py` for temporary HTTP servers instead of duplicating setup/teardown code.

Run focused tests during development, then run the full suite:

```bash
python -m pytest -q tests/test_json_demo.py
python -m pytest -q
```

## Commit & Pull Request Guidelines

Recent commits use short imperative subjects, for example `Add perceptionDemo` and `Update gitignore & readme`. Keep commit messages concise and behavior-focused.

Pull requests should include a short description, relevant TODO/issue context, test results, and screenshots or GIFs for UI changes. For protocol changes, mention affected request/response shapes.

## Security & Configuration Tips

The platform calls external algorithm services from `config.yaml`; do not hard-code service URLs in components. Use `ctx.render_client`, `ctx.health_client`, and `ctx.component_resource_path(...)`. Do not send local file paths to algorithm servers; package file contents into the agreed payload format.

## Think before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## Complete The Tasks Listed in TODO.md
- 每次启动时，或任务结束后，先检查 TODO.md中是否还有未完成的任务
- 若存在未完成任务，继续调用TDD Skill进行功能开发
- 当出现错误时中止，等待下一步指令

