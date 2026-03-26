"""macOS .pkg builder for raw release folders."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from ..config import Config
from .common import _sanitise_name, log
from .mac_support import _bundle_identifier, _create_pkg_from_root, _finalize_mac_output, _prepare_mac_source


def _pkg_payload_dir_name(app_name: str) -> str:
    return _sanitise_name(app_name) or "app"


def _write_pkg_launcher(pkg_root: str, payload_dir_name: str, app_exec: str) -> None:
    launcher_name = Path(app_exec).name
    launcher_dir = os.path.join(pkg_root, "usr", "local", "bin")
    launcher_path = os.path.join(launcher_dir, launcher_name)
    os.makedirs(launcher_dir, exist_ok=True)
    with open(launcher_path, "w") as handle:
        handle.write(
            "#!/bin/bash\n"
            'DIR="$(cd "$(dirname "$0")/../../../opt/' + payload_dir_name + '" && pwd)"\n'
            f'exec "${{DIR}}/{app_exec}" "$@"\n'
        )
    os.chmod(launcher_path, 0o755)


def _stage_pkg_root(source: str, cfg: Config, temp_root: str) -> str:
    pkg_root = os.path.join(temp_root, "pkg-root")
    payload_dir_name = _pkg_payload_dir_name(cfg.app_name)
    payload_root = os.path.join(pkg_root, "opt", payload_dir_name)
    os.makedirs(os.path.dirname(payload_root), exist_ok=True)
    shutil.copytree(source, payload_root)

    if cfg.app_exec:
        _write_pkg_launcher(pkg_root, payload_dir_name, cfg.app_exec)

    return pkg_root


def build_pkg(cfg: Config) -> str:
    output_file = cfg.output + ".pkg"
    identifier = _bundle_identifier(cfg.app_name, ".pkg")
    log.info("Creating PKG: %s", output_file)

    temp_root = tempfile.mkdtemp(prefix="easyinstaller-pkg-")
    signed_source_root = None
    if cfg.mac_notarize:
        signed_source_root = _prepare_mac_source(cfg, "easyinstaller-pkg-src-")
    try:
        staged_root = _stage_pkg_root(signed_source_root or cfg.source, cfg, temp_root)
        result = _create_pkg_from_root(staged_root, output_file, "/", identifier, cfg.app_version, cfg)
    finally:
        if signed_source_root is not None:
            shutil.rmtree(signed_source_root, ignore_errors=True)
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)

    _finalize_mac_output(cfg, result)
    log.info("Created: %s", output_file)
    return result
