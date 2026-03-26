"""tar.gz builder."""

from __future__ import annotations

import os
import shutil
import tarfile

from ..config import Config
from .common import log
from .mac_support import _finalize_mac_output, _prepare_mac_source


def _build_tar_gz_from_source(source: str, output_file: str) -> str:
    with tarfile.open(output_file, "w:gz") as tf:
        for entry in sorted(os.listdir(source)):
            tf.add(os.path.join(source, entry), arcname=entry)
    return output_file


def build_tar_gz(cfg: Config) -> str:
    output_file = cfg.output + ".tar.gz"
    log.info("Creating tar.gz archive: %s", output_file)

    temp_root = None
    source = cfg.source
    if cfg.target_os == "mac" and cfg.mac_notarize:
        temp_root, source = _prepare_mac_source(cfg, "easyinstaller-mac-targz-")
    try:
        result = _build_tar_gz_from_source(source, output_file)
    finally:
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)

    _finalize_mac_output(cfg, result)
    log.info("Created: %s", result)
    return result
