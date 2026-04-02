"""app-in-dmg builder."""

from __future__ import annotations

import os
import shutil
import tempfile

from ..config import Config
from .common import log
from .mac_support import (
    _create_app_bundle,
    _create_applications_alias,
    _create_styled_app_dmg_image,
    _finalize_mac_output,
    _prepare_mac_source,
)


def build_app_in_dmg(cfg: Config) -> str:
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for .app bundles")
    dmg_output = cfg.output + ".dmg"
    log.info("Creating app-in-dmg: %s", dmg_output)

    temp_root = tempfile.mkdtemp(prefix="easyinstaller-app-in-dmg-")
    signed_source_root = None
    if cfg.mac_notarize:
        signed_source_root = _prepare_mac_source(cfg, "easyinstaller-app-in-dmg-src-")
    try:
        app_path = os.path.join(temp_root, f"{cfg.app_name}.app")
        _create_app_bundle(cfg, signed_source_root or cfg.source, app_path)
        _create_applications_alias(temp_root)
        _create_styled_app_dmg_image(temp_root, dmg_output, cfg.app_name, f"{cfg.app_name}.app")
    finally:
        if signed_source_root is not None:
            shutil.rmtree(signed_source_root, ignore_errors=True)
        shutil.rmtree(temp_root, ignore_errors=True)

    _finalize_mac_output(cfg, dmg_output)
    log.info("Created: %s", dmg_output)
    return dmg_output
