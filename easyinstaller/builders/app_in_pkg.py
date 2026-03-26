"""macOS app-in-pkg builder."""

from __future__ import annotations

import shutil
import tempfile

from ..config import Config
from .common import log
from .mac_support import (
    _bundle_identifier,
    _create_app_bundle,
    _create_pkg_from_component,
    _finalize_mac_output,
    _prepare_mac_source,
)


def build_app_in_pkg(cfg: Config) -> str:
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for .app bundles")

    output_file = cfg.output + ".pkg"
    log.info("Creating app-in-pkg: %s", output_file)

    temp_root = tempfile.mkdtemp(prefix="easyinstaller-app-in-pkg-")
    signed_source_root = None
    source = cfg.source
    if cfg.mac_notarize:
        signed_source_root, source = _prepare_mac_source(cfg, "easyinstaller-app-in-pkg-src-")
    try:
        app_path = _create_app_bundle(cfg, source, f"{temp_root}/{cfg.app_name}.app")
        result = _create_pkg_from_component(
            app_path,
            output_file,
            "/Applications",
            _bundle_identifier(cfg.app_name) + ".pkg",
            cfg.app_version,
            cfg,
        )
    finally:
        if signed_source_root is not None:
            shutil.rmtree(signed_source_root, ignore_errors=True)
        shutil.rmtree(temp_root, ignore_errors=True)

    _finalize_mac_output(cfg, result)
    log.info("Created: %s", result)
    return result
