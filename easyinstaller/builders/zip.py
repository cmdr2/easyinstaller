"""ZIP builder."""

from __future__ import annotations

import os
import shutil
import zipfile

from ..config import Config
from .common import log
from .mac_support import _finalize_mac_output, _prepare_mac_source


def _build_zip_from_source(source: str, output_file: str) -> str:
    base_name = os.path.basename(source)
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(source):
            if not filenames and not dirnames:
                arc_dir = os.path.join(base_name, os.path.relpath(dirpath, source)) + "/"
                zf.writestr(zipfile.ZipInfo(arc_dir), "")
            for filename in filenames:
                abs_path = os.path.join(dirpath, filename)
                arc_name = os.path.join(base_name, os.path.relpath(abs_path, source))
                zf.write(abs_path, arc_name)
    return output_file


def build_zip(cfg: Config) -> str:
    output_file = cfg.output + ".zip"
    log.info("Creating zip archive: %s", output_file)

    temp_root = None
    source = cfg.source
    if cfg.target_os == "mac" and cfg.mac_notarize:
        temp_root, source = _prepare_mac_source(cfg, "easyinstaller-mac-zip-")
    try:
        result = _build_zip_from_source(source, output_file)
    finally:
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)

    _finalize_mac_output(cfg, result)
    log.info("Created: %s", result)
    return result