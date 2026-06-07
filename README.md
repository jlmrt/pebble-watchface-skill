# Pebble Watchface Codex Skill

A Codex skill for creating Pebble watchfaces.

It helps Codex scaffold projects, write Pebble C and PebbleKit JS, build `.pbw` files, run emulator checks, capture screenshots, and package final watchface artifacts.

Default target: **Emery** (Pebble Time 2, 200x228 color display).

## Install

After this repository is published, install the skill with Codex:

```text
$skill-installer install https://github.com/<owner>/<repo>/tree/main/pebble-watchface
```

Restart Codex after installation.

Manual install:

```bash
mkdir -p "$HOME/.agents/skills"
cp -R pebble-watchface "$HOME/.agents/skills/pebble-watchface"
```

## Use

Start a new Codex thread and describe the watchface you want.

Examples:

```text
Create a cozy garden watchface for Emery with time, date, battery, and a plant that changes throughout the day.
```

```text
Build a crisp art-deco analog watchface for Emery with strong contrast and a small date sidebar.
```

```text
Make a playful tide-pool watchface for Emery with minute-based bubbles, weather, and readable digital time.
```

## Privacy And Security Notes

- The skill does not include API keys, tokens, passwords, or credential files.
- Weather templates use Open-Meteo because it does not require an API key.
- Weather projects request phone location permission and send approximate coordinates, rounded to 2 decimal places, to Open-Meteo for weather lookup.
- Publish from a fresh repository created from the current tree, or rewrite local history first, if earlier commits contain private metadata or removed sample assets.
- The Clay tutorial pins `@rebble/clay` to a fixed version to reduce dependency drift.

## Requirements

For full build and verification:

- Pebble SDK
- Emery emulator
- Python 3
- Pillow for icon and GIF helpers

```bash
pip3 install Pillow
```
