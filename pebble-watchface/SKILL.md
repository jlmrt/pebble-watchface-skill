---
name: pebble-watchface
description: Create complete Pebble smartwatch watchfaces and watchapps from natural-language briefs. Use when Codex is asked to design, implement, build, test, visually verify, package, preview, or publish Pebble watchfaces, Pebble apps, PBW artifacts, PebbleKit JS weather/data integrations, QEMU emulator workflows, or Pebble C UI/animation code.
---

# Pebble Watchface

Build complete Pebble watchfaces with source code, `package.json`, `wscript`, a compiled `.pbw`, emulator screenshots, and optional preview assets. Default to **emery** (Pebble Time 2, 200x228 rectangular, 64-color) unless the user asks for another platform.

## Core Rules

- Deliver a buildable project, not only snippets. A normal request should end with a `.pbw`, an emulator screenshot, and a concise description of what was verified.
- Use `MINUTE_UNIT` for `tick_timer_service_subscribe()` unless the user explicitly asks for seconds. `SECOND_UNIT` drains battery quickly.
- Use short `app_timer_register()` loops only for brief interactions or limited animation bursts. Continuous sub-second animation is acceptable only when explicitly requested.
- Use `layer_get_bounds()` for screen dimensions. Avoid hardcoding 144x168 or 200x228 inside draw code except in design notes and validation calculations.
- Use fixed-point Pebble math: `sin_lookup()`, `cos_lookup()`, `TRIG_MAX_ANGLE`, and integer arithmetic. Avoid `float` and `double`.
- Pre-allocate persistent `GPath` objects in `window_load`; destroy them in `window_unload`.
- Register AppMessage callbacks before `app_message_open()`.
- Keep all visual elements inside the target bounds. For emery, x must fit within `0..199` and y within `0..227`.
- When making user-facing changes to an existing app, bump `package.json` `version` before the final rebuild unless the user explicitly says not to. After rebuilding, verify both `build/appinfo.json` and the `.pbw` archive contain the expected `versionLabel`.

## Resource Map

- `scripts/create_project.py`: scaffold a Pebble project from bundled templates.
- `scripts/validate_project.py`: validate required files, manifest structure, and common C issues before build.
- `scripts/generate_uuid.py`: generate a Pebble manifest UUID.
- `scripts/create_app_icons.py`: create `icon_80x80.png` and `icon_144x144.png` from a screenshot.
- `scripts/create_preview_gif.py`: capture emulator frames into `preview_<platform>.gif`; requires Pillow and a running emulator.
- `templates/`: C, JavaScript, package, and wscript templates for animated, static, and weather watchfaces.
- `references/pebble-api-reference.md`: API reminders for layers, drawing, AppMessage, time, battery, and services.
- `references/drawing-guide.md`: layout, GPath, text, color, and drawing-order patterns.
- `references/animation-patterns.md`: battery-aware animation patterns and particle/motion examples.
- `assets/sample-projects/`: working watchface examples to inspect for richer visual implementations.
- `assets/tutorials/c-watchface-tutorial/`: tutorial projects, including basic time/date, weather, and Clay settings examples.

Read only the reference files relevant to the request. For weather/data watchfaces, read `references/pebble-api-reference.md` plus `assets/tutorials/c-watchface-tutorial/part4/`. For animated or artistic watchfaces, read `references/animation-patterns.md`, `references/drawing-guide.md`, and one nearby sample under `assets/sample-projects/`.

## Workflow

1. Clarify only genuinely blocking details. If the brief is underspecified, choose sensible defaults: digital or illustrative time display, optional date, no weather unless asked, emery target.
2. Plan the layout before writing code. Calculate y positions, heights, x positions, widths, and bottom/right edges for each element.
3. Scaffold or create the project.
4. Implement complete source files.
5. For existing projects with user-facing changes, increment the app version in `package.json`, usually the patch number.
6. Validate, clean when package metadata changed, build, and fix errors.
7. Verify the `.pbw` archive version before installing, copying to `releases/`, or publishing.
8. Install in QEMU, capture screenshots, visually inspect them, and iterate until the result matches the brief.
9. Generate icons and preview GIFs when useful.
10. Report final artifact paths, verification status, version confirmation, and install commands.

Use subagents for independent research/design if they are available and the request is complex. If subagents are unavailable, do the research and design directly.

## Project Creation

Prefer the scaffold script for new projects:

```bash
python3 /path/to/pebble-watchface/scripts/create_project.py "Project Name" \
  --animated \
  --author "Author Name" \
  --display "Display Name" \
  --output /path/to/output
```

Template flags:

- `--animated`: animated/artistic canvas template.
- `--static`: static or analog-style template.
- `--weather`: weather/data template with `src/pkjs/index.js`, AppMessage keys, and location capability.

Required project files:

- `package.json` with `pebble.watchapp.watchface: true`, a valid UUID, and `"targetPlatforms": ["emery"]` by default.
- `wscript` using `ctx.pbl_build(..., bin_type='app')` and `ctx.pbl_bundle(...)`.
- `src/c/main.c` with `#include <pebble.h>`, `init()`, `deinit()`, and `main()`.
- `src/pkjs/index.js` only for weather/web data.
- `resources/` for fonts/images, even if empty.

## Implementation Notes

For every C watchface:

- Create the main `Window`, assign load/unload handlers, push it, subscribe to minute ticks, update time immediately, and enter `app_event_loop()`.
- Destroy `Window`, `TextLayer`, `BitmapLayer`, `GBitmap`, `Layer`, `GPath`, timers, and service subscriptions in cleanup paths.
- Use `static` module state for layers and cached display strings.
- Use `layer_mark_dirty()` after time/data changes that affect custom drawing.
- Use `PBL_COLOR` guards for color-specific palettes and B&W fallbacks.
- For custom text drawing, use boxes sized for the longest expected string and `GTextOverflowModeTrailingEllipsis` or `GTextOverflowModeWordWrap`.

For weather or web data:

- Use the AppMessage + PebbleKit JS pattern: watch C code sends requests, phone-side `src/pkjs/index.js` fetches data, then sends values back with `Pebble.sendAppMessage()`.
- Prefer Open-Meteo for weather because it is free and does not require an API key.
- Disclose location use when adding weather: PebbleKit JS requests phone location permission and sends approximate coordinates to the weather provider.
- Round coordinates before network requests, or use a user-provided city/location setting. Do not log, store, or transmit exact coordinates unless the user explicitly asks.
- Refresh weather on startup and at coarse intervals such as every 30 minutes.
- Add `"capabilities": ["location"]` and message keys such as `TEMPERATURE`, `CONDITIONS`, and `REQUEST_WEATHER` to `package.json`.

## Build And Verify

### Version Packaging

For edits to an existing watchface or app, check `package.json` before the final build:

- If the visible behavior, settings, resources, or user-facing UI changed, increment `version`, usually by one patch version such as `1.0.2` to `1.0.3`.
- If the user already bumped the version, do not bump it again.
- Rebuild after the bump. Pebble packages the app version from `package.json`, so rebuilding before the bump leaves the installed settings/app screen showing the old version.
- After any `package.json` version or package metadata change, run `pebble clean` before `pebble build`. Pebble can leave an old `appinfo.json` embedded inside an existing `.pbw` even when `build/appinfo.json` has updated.
- After `pebble build`, confirm `build/appinfo.json` contains the expected `versionLabel`.
- Verify the actual `.pbw` archive before install, release copy, or publish:

```bash
unzip -p build/<app>.pbw appinfo.json | rg 'versionLabel'
```

- Only install or copy to `releases/` after the zipped `.pbw` itself shows the expected version.

Run local validation first:

```bash
python3 /path/to/pebble-watchface/scripts/validate_project.py /path/to/watchface
```

Then build:

```bash
cd /path/to/watchface
pebble clean   # Required after version/package metadata changes
pebble build
```

If build fails, read the compiler output, patch the code, and repeat until `build/*.pbw` exists.

Install and screenshot in QEMU:

```bash
pebble install --emulator emery
pebble screenshot --no-open --emulator emery screenshot_emery.png
pebble logs --emulator emery
```

At most once per session, ask whether the user wants successful builds installed to a physical Pebble through the phone IP. Do not block emulator/PBW delivery while waiting for this. If the user opts in and provides an IP, install the verified PBW with:

```bash
pebble install --phone 192.168.x.x build/<app>.pbw
```

If the emery emulator is not installed, run:

```bash
pebble sdk install-emulator emery
```

Use the available image inspection tool to view `screenshot_emery.png`. The verification pass must check:

- No clipping at screen edges.
- Text is readable and not truncated.
- Time/date/data positions match the planned layout.
- Main theme is recognizable.
- Colors and contrast are legible on the target platform.
- Logs show no crash, exception, or important warning.

If any check fails, patch, rebuild, reinstall, screenshot again, and re-check.

## Assets And Publishing

After visual verification:

```bash
python3 /path/to/pebble-watchface/scripts/create_app_icons.py /path/to/watchface
python3 /path/to/pebble-watchface/scripts/create_preview_gif.py /path/to/watchface --frames 8 --delay 400
```

Publishing is optional and should only happen when the user asks:

```bash
pebble login
pebble publish
```

For non-interactive publishing:

```bash
pebble publish --non-interactive \
  --description "Short watchface description" \
  --release-notes "Initial release"
```

## Delivery

In the final response, include:

- `.pbw` path, usually `build/<name>.pbw`.
- Screenshot path, usually `screenshot_emery.png`.
- Preview GIF and icon paths if generated.
- Confirmed app version, including `package.json` `version` and `build/appinfo.json` `versionLabel` when available.
- A short visual confirmation of what was inspected.
- Install commands:

```bash
pebble install --emulator emery
pebble install --cloudpebble
```

Mention any blocked step clearly, such as missing Pebble SDK, missing emulator, or unavailable Pillow.
