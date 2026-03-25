"""Snap builder."""

from __future__ import annotations

import os
import shutil
import tempfile

from ..config import Config
from .common import _require, _run, _sanitise_name, log


SNAP_BASE = "core24"


def build_snap(cfg: Config) -> str:
    _require("snapcraft")
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for Snap")

    output_file = cfg.output + ".snap"
    log.info("Creating Snap: %s", output_file)

    sanitised = _sanitise_name(cfg.app_name)
    snap_dir = tempfile.mkdtemp(prefix="easyinstaller-snap-")
    try:
        shutil.copytree(cfg.source, os.path.join(snap_dir, "source"))
        snap_meta = os.path.join(snap_dir, "snap")
        os.makedirs(snap_meta)

        with open(os.path.join(snap_meta, "snapcraft.yaml"), "w") as handle:
            handle.write(
                f"name: {sanitised}\n"
                f"version: '{cfg.app_version}'\n"
                f"summary: {cfg.app_description}\n"
                f"description: |\n"
                f"  {cfg.app_description}\n"
                f"base: {SNAP_BASE}\n"
                f"grade: stable\n"
                f"confinement: strict\n"
                f"\n"
                f"parts:\n"
                f"  {sanitised}:\n"
                f"    plugin: dump\n"
                f"    source: source/\n"
                f"\n"
                f"apps:\n"
                f"  {sanitised}:\n"
                f"    command: {cfg.app_exec}\n"
            )

        _run(["snapcraft", "pack", "--destructive-mode"], cwd=snap_dir)

        built = None
        for filename in os.listdir(snap_dir):
            if filename.endswith(".snap"):
                built = os.path.join(snap_dir, filename)
                break
        if not built:
            raise RuntimeError("Snap build failed - no output found")
        shutil.copy2(built, output_file)
    finally:
        shutil.rmtree(snap_dir, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file
