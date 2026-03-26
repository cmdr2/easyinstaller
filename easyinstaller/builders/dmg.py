"""DMG builder."""

from __future__ import annotations

import os
import shutil
import tempfile

from ..config import Config
from .common import log
from .mac_support import _create_dmg_image, _finalize_mac_output, _prepare_mac_source


def build_dmg(cfg: Config) -> str:
    output_file = cfg.output + ".dmg"
    log.info("Creating DMG: %s", output_file)

    if cfg.mac_notarize:
        temp_root = _prepare_mac_source(cfg, "easyinstaller-dmg-")
    else:
        temp_root = tempfile.mkdtemp(prefix="easyinstaller-dmg-")
        shutil.copytree(cfg.source, temp_root, dirs_exist_ok=True)
    try:
        _create_dmg_image(temp_root, output_file, cfg.app_name)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    _finalize_mac_output(cfg, output_file)
    log.info("Created: %s", output_file)
    return output_file
