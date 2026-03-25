"""macOS .app builder."""

from __future__ import annotations

import shutil

from ..config import Config
from .common import log
from .mac_support import _create_app_bundle, _finalize_mac_output, _prepare_mac_source


def build_app(cfg: Config) -> str:
    output_file = cfg.output + ".app"
    log.info("Creating .app bundle: %s", output_file)

    temp_root = None
    source = cfg.source
    if cfg.mac_notarize:
        temp_root, source = _prepare_mac_source(cfg, "easyinstaller-mac-app-src-")
    try:
        result = _create_app_bundle(cfg, source, output_file)
    finally:
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)

    _finalize_mac_output(cfg, result)
    log.info("Created: %s", result)
    return result
