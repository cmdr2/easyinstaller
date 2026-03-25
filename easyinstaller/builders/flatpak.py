"""Flatpak builder."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from ..config import Config
from .common import _flatpak_arch, _require, _run, _sanitise_name, log


def build_flatpak(cfg: Config) -> str:
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for Flatpak")
    _require("flatpak")
    _require("flatpak-builder")

    output_file = cfg.output + ".flatpak"
    log.info("Creating Flatpak: %s", output_file)

    import json
    import re

    sanitised_id = "com." + re.sub(r"[^a-z0-9]", "", cfg.app_name.lower()) + ".app"

    build_dir = tempfile.mkdtemp(prefix="easyinstaller-flatpak-")
    try:
        src_copy = os.path.join(build_dir, "source")
        shutil.copytree(cfg.source, src_copy)

        subprocess.run(
            [
                "flatpak",
                "remote-add",
                "--user",
                "--if-not-exists",
                "flathub",
                "https://dl.flathub.org/repo/flathub.flatpakrepo",
            ],
            check=False,
        )
        subprocess.run(
            [
                "flatpak",
                "install",
                "--user",
                "-y",
                "flathub",
                "org.freedesktop.Platform//23.08",
                "org.freedesktop.Sdk//23.08",
            ],
            check=False,
        )

        manifest = {
            "app-id": sanitised_id,
            "runtime": "org.freedesktop.Platform",
            "runtime-version": "23.08",
            "sdk": "org.freedesktop.Sdk",
            "command": cfg.app_exec,
            "modules": [
                {
                    "name": _sanitise_name(cfg.app_name),
                    "buildsystem": "simple",
                    "build-commands": ["mkdir -p /app/bin", "cp -a . /app/bin/"],
                    "sources": [{"type": "dir", "path": "source"}],
                }
            ],
        }
        manifest_path = os.path.join(build_dir, "manifest.json")
        with open(manifest_path, "w") as handle:
            json.dump(manifest, handle, indent=2)

        fp_arch = _flatpak_arch(cfg.arch)
        _run(
            [
                "flatpak-builder",
                "--user",
                "--force-clean",
                "--arch",
                fp_arch,
                os.path.join(build_dir, "build"),
                manifest_path,
            ]
        )
        _run(
            [
                "flatpak",
                "build-export",
                "--arch",
                fp_arch,
                os.path.join(build_dir, "repo"),
                os.path.join(build_dir, "build"),
            ]
        )
        _run(["flatpak", "build-bundle", "--arch", fp_arch, os.path.join(build_dir, "repo"), output_file, sanitised_id])
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file
