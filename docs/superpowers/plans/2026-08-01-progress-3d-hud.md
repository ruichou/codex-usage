# Progress 3D HUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat Tkinter orb renderer with a compact 3D glass-and-metal HUD that matches the supplied reference while preserving the existing Codex usage reader.

**Architecture:** Keep `fetch_usage`, `parse_usage`, and `format_reset` unchanged. Add a `Progress3D` renderer that accepts progress, status, and reset text, renders a supersampled Pillow image with layered metal/glass/glow shapes, and displays it in the existing transparent Tkinter window. The window remains responsible only for drag, controls, refresh scheduling, and background I/O.

**Tech Stack:** Python 3, Tkinter, Pillow, PyInstaller, unittest.

## Global Constraints

- Do not change the Codex authentication or usage endpoint logic.
- Keep the widget always-on-top, draggable, transparent around the orb, and packaged for Windows/macOS.
- Use 4× supersampling and downsampling for anti-aliased edges.
- Use a single 600ms ease-out refresh animation; no particles or bounce.
- Keep the UI text in Chinese where the existing app uses Chinese copy.

## File Map

- Modify `usage_widget.py`: add `Progress3D`, animation state, and replace the old Canvas arc renderer.
- Modify `tests/test_usage_widget.py`: test renderer inputs, color thresholds, animation endpoints, and existing business parsing.
- Modify `build.ps1`: ensure the Pillow dependency is available to PyInstaller builds.
- Modify `README.md`: document the new Pillow-backed renderer only if installation/build prerequisites change.

### Task 1: Define renderer contract and failing tests

- [ ] Add tests for `Progress3D` state normalization: progress is clamped to 0–100 and reset text is preserved.
- [ ] Add tests for the existing color thresholds and animation endpoint calculation.
- [ ] Run `python -m unittest discover -s tests -v` and confirm the new tests fail because the renderer API is not present.

### Task 2: Implement the supersampled 3D renderer

- [ ] Add `Progress3D(canvas, size)` with `set_state(progress, status, reset_text, color)` and `animate_to(progress, status, reset_text, color, done=None)`.
- [ ] Render at 4× size using Pillow layers: shadow, metal rings, glass gradient, inner bevel, dark remaining ring, glowing progress arc, embossed percentage, status text, and rounded blue time capsule.
- [ ] Use Gaussian blur only for soft glow/shadow layers; composite before downsampling with `Image.Resampling.LANCZOS`.
- [ ] Keep the rendered image reference alive on the Tkinter canvas to prevent garbage collection.

### Task 3: Integrate without changing usage logic

- [ ] Replace `_draw_sphere` and Canvas text items with `Progress3D` state updates.
- [ ] Fix the stale `self.plan.config()` call in `refresh()` by updating renderer state instead.
- [ ] Preserve background-thread fetch and Tkinter main-thread updates.
- [ ] Keep minimize/close controls in the transparent outer area and bind dragging to the canvas.

### Task 4: Add animation and state transitions

- [ ] Animate startup from 0 to the fetched percentage over 600ms.
- [ ] Animate refresh updates from the current percentage to the new percentage over 600ms.
- [ ] Fade the center number and time capsule through the renderer's alpha parameter without adding particles or bounce.
- [ ] Show error state as `--`, red accent, and readable reset/error text.

### Task 5: Verify and package

- [ ] Run the full unittest suite and `python -m py_compile usage_widget.py`.
- [ ] Build `dist/CodexUsageWidget.exe` with PyInstaller and run a short startup smoke test.
- [ ] Capture or inspect a local running screenshot at the widget's actual size and compare against the supplied reference for ring, glass, capsule, and text hierarchy.
- [ ] Update README/build prerequisites if Pillow is not already bundled, then commit and push the verified package.
