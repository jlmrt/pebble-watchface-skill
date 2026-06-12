#!/usr/bin/env python3
"""
Pebble Watchface Project Creator

Creates a new Pebble watchface project with the correct structure
and configuration files.

Usage:
    python create_project.py <project_name> [options]

Options:
    --animated    Use animated watchface template (explicit opt-in)
    --static      Use static/analog watchface template
    --weather     Use weather watchface template (includes pkjs)
    --author      Author name
    --display     Display name for the watchface
    --project-dir Use this exact project directory if missing or empty
    --targets     Comma-separated target platforms, default: emery
"""

import argparse
import json
import re
import shutil
import sys
import uuid
from pathlib import Path


VALID_TARGETS = ['aplite', 'basalt', 'chalk', 'diorite', 'emery', 'flint', 'gabbro']


def slugify(name):
    """Convert name to a valid slug"""
    slug = re.sub(r'[^a-z0-9]+', '-', name.strip().lower())
    return slug.strip('-')


def generate_uuid():
    """Generate a random UUID for the watchface"""
    return str(uuid.uuid4())


def parse_targets(value):
    """Parse and validate a comma-separated Pebble target platform list."""
    requested = []
    for raw_target in value.split(','):
        target = raw_target.strip().lower()
        if not target:
            raise argparse.ArgumentTypeError('target list contains an empty value')
        if target not in VALID_TARGETS:
            valid = ','.join(VALID_TARGETS)
            raise argparse.ArgumentTypeError(f'invalid target platform: {target} (valid: {valid})')
        if target in requested:
            raise argparse.ArgumentTypeError(f'duplicate target platform: {target}')
        requested.append(target)

    return [target for target in VALID_TARGETS if target in requested]


def is_empty_dir(path):
    """Return true when path is an existing empty directory."""
    return path.is_dir() and not any(path.iterdir())


def create_package_json(project_path, name, display_name, author, template_type='static', targets=None):
    """Create package.json file"""
    targets = targets or ['emery']
    content = {
        "name": slugify(name),
        "author": author,
        "version": "1.0.0",
        "keywords": ["pebble-app"],
        "private": True,
        "dependencies": {},
        "pebble": {
            "displayName": display_name,
            "uuid": generate_uuid(),
            "sdkVersion": "3",
            "enableMultiJS": True,
            "targetPlatforms": targets,
            "watchapp": {
                "watchface": True
            },
            "resources": {
                "media": []
            }
        }
    }

    # Weather projects need messageKeys and location capability
    if template_type == 'weather':
        content["pebble"]["capabilities"] = ["location"]
        content["pebble"]["messageKeys"] = ["TEMPERATURE", "CONDITIONS", "REQUEST_WEATHER"]

    with open(project_path / 'package.json', 'w') as f:
        json.dump(content, f, indent=2)

    print(f"  Created package.json")


def create_wscript(project_path):
    """Create wscript build file"""
    content = """#
# Pebble wscript build configuration
#
import os.path

top = '.'
out = 'build'


def options(ctx):
    ctx.load('pebble_sdk')


def configure(ctx):
    ctx.load('pebble_sdk')


def build(ctx):
    ctx.load('pebble_sdk')

    build_worker = os.path.exists('worker_src')
    binaries = []

    cached_env = ctx.env
    for platform in ctx.env.TARGET_PLATFORMS:
        ctx.env = ctx.all_envs[platform]
        ctx.set_group(ctx.env.PLATFORM_NAME)
        app_elf = '{}/pebble-app.elf'.format(ctx.env.BUILD_DIR)
        ctx.pbl_build(source=ctx.path.ant_glob('src/c/**/*.c'),
                      target=app_elf, bin_type='app')

        if build_worker:
            worker_elf = '{}/pebble-worker.elf'.format(ctx.env.BUILD_DIR)
            binaries.append({'platform': platform, 'app_elf': app_elf,
                             'worker_elf': worker_elf})
            ctx.pbl_build(source=ctx.path.ant_glob('worker_src/c/**/*.c'),
                          target=worker_elf, bin_type='worker')
        else:
            binaries.append({'platform': platform, 'app_elf': app_elf})
    ctx.env = cached_env

    ctx.set_group('bundle')
    ctx.pbl_bundle(binaries=binaries,
                   js=ctx.path.ant_glob(['src/pkjs/**/*.js',
                                         'src/pkjs/**/*.json']),
                   js_entry_file='src/pkjs/index.js')
"""
    with open(project_path / 'wscript', 'w') as f:
        f.write(content)

    print(f"  Created wscript")


def create_gitignore(project_path):
    """Create .gitignore file"""
    content = """# Build artifacts
build/

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Pebble SDK
.pebble-sdk/
"""
    with open(project_path / '.gitignore', 'w') as f:
        f.write(content)

    print(f"  Created .gitignore")


def copy_template(project_path, template_type, skill_path):
    """Copy the appropriate template file"""
    c_templates = {
        'animated': 'animated-watchface.c',
        'static': 'static-watchface.c',
        'weather': 'weather-watchface.c'
    }

    template_file = c_templates.get(template_type, 'static-watchface.c')
    template_path = skill_path / 'templates' / template_file

    # C project structure
    c_dir = project_path / 'src' / 'c'
    c_dir.mkdir(parents=True, exist_ok=True)

    if template_path.exists():
        shutil.copy(template_path, c_dir / 'main.c')
        print(f"  Created src/c/main.c from {template_file}")
    else:
        with open(c_dir / 'main.c', 'w') as f:
            f.write('#include <pebble.h>\n\nint main(void) {\n    app_event_loop();\n    return 0;\n}\n')
        print(f"  Created src/c/main.c (minimal)")

    # Weather template also needs pkjs
    if template_type == 'weather':
        pkjs_dir = project_path / 'src' / 'pkjs'
        pkjs_dir.mkdir(parents=True, exist_ok=True)
        pkjs_template = skill_path / 'templates' / 'pkjs-weather.js'
        if pkjs_template.exists():
            shutil.copy(pkjs_template, pkjs_dir / 'index.js')
            print(f"  Created src/pkjs/index.js from pkjs-weather.js")
        else:
            with open(pkjs_dir / 'index.js', 'w') as f:
                f.write("// PebbleKit JS\nPebble.addEventListener('ready', function() {});\n")
            print(f"  Created src/pkjs/index.js (minimal)")


def main():
    parser = argparse.ArgumentParser(description='Create a new Pebble watchface project')
    parser.add_argument('name', help='Project name')
    template_group = parser.add_mutually_exclusive_group()
    template_group.add_argument('--animated', action='store_true', help='Use animated template (explicit opt-in)')
    template_group.add_argument('--static', action='store_true', help='Use static/analog template (default)')
    template_group.add_argument('--weather', action='store_true', help='Use weather template (includes pkjs)')
    parser.add_argument('--author', default='Your Name', help='Author name')
    parser.add_argument('--display', default=None, help='Display name')
    parser.add_argument('--output', '-o', default='.', help='Output directory')
    parser.add_argument('--project-dir', default=None,
                        help='Use this exact project directory if it does not exist or is empty')
    parser.add_argument('--targets', type=parse_targets, default=parse_targets('emery'),
                        help='Comma-separated target platforms (default: emery)')

    args = parser.parse_args()

    # Determine template type
    if args.animated:
        template_type = 'animated'
    elif args.weather:
        template_type = 'weather'
    else:
        template_type = 'static'

    display_name = args.display or args.name

    # Resolve project directory
    project_slug = slugify(args.name)

    if not project_slug:
        print("Error: Project name must contain at least one letter or number")
        sys.exit(1)

    if args.project_dir:
        project_path = Path(args.project_dir).expanduser().resolve()
    else:
        output_path = Path(args.output).expanduser().resolve()
        project_path = (output_path / project_slug).resolve()
        try:
            project_path.relative_to(output_path)
        except ValueError:
            print(f"Error: Project path must stay inside output directory: {output_path}")
            sys.exit(1)

    if project_path.exists() and not project_path.is_dir():
        print(f"Error: Project path exists and is not a directory: {project_path}")
        sys.exit(1)

    if project_path.exists() and not is_empty_dir(project_path):
        print(f"Error: Directory already exists and is not empty: {project_path}")
        sys.exit(1)

    print(f"\nCreating Pebble watchface project: {args.name}")
    print(f"Template: {template_type}")
    print(f"Targets: {', '.join(args.targets)}")
    print(f"Location: {project_path}\n")

    # Create directories
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / 'resources' / 'fonts').mkdir(parents=True)
    (project_path / 'resources' / 'images').mkdir(parents=True)

    # Find skill path (for templates)
    script_path = Path(__file__).resolve().parent
    skill_path = script_path.parent

    # Create files
    create_package_json(project_path, args.name, display_name, args.author, template_type, args.targets)
    create_wscript(project_path)
    create_gitignore(project_path)
    copy_template(project_path, template_type, skill_path)

    print(f"\n✓ Project created successfully!")
    print(f"\nNext steps:")
    print(f"  1. cd {project_path}")
    print(f"  2. Edit src/c/main.c (or src/pkjs/index.js)")
    print(f"  3. pebble build")
    print(f"  4. pebble install --emulator {args.targets[0]}")


if __name__ == '__main__':
    main()
