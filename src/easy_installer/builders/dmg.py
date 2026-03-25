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

    temp_root = None
    source = cfg.source
    if cfg.mac_notarize:
        temp_root, source = _prepare_mac_source(cfg, "easyinstaller-dmg-")
    else:
        temp_root = tempfile.mkdtemp(prefix="easyinstaller-dmg-")
        source = os.path.join(temp_root, os.path.basename(cfg.source))
        shutil.copytree(cfg.source, source)
    try:
        _create_dmg_image(source, output_file, cfg.app_name)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    _finalize_mac_output(cfg, output_file)
    log.info("Created: %s", output_file)
    return output_file
