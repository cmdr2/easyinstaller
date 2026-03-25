"""Builder functions, one per target type."""

from __future__ import annotations

import os
from typing import Callable

from ..config import Config
from .app import build_app
from .app_in_dmg import build_app_in_dmg
from .appimage import build_appimage
from .common import _appimage_arch, _flatpak_arch, _host_arch, _sanitise_name
from .deb import build_deb
from .dmg import build_dmg
from .flatpak import build_flatpak
from .nsis import _NSIS_TEMPLATE, build_nsis
from .rpm import build_rpm
from .snap import build_snap
from .tar_gz import build_tar_gz
from .zip import build_zip

BUILDERS: dict[str, Callable[[Config], str]] = {
    "zip": build_zip,
    "tar.gz": build_tar_gz,
    "nsis": build_nsis,
    "deb": build_deb,
    "rpm": build_rpm,
    "appimage": build_appimage,
    "flatpak": build_flatpak,
    "snap": build_snap,
    "dmg": build_dmg,
    "app": build_app,
    "app-in-dmg": build_app_in_dmg,
}


def build(cfg: Config) -> str:
    """Dispatch to the appropriate builder based on *cfg.target_type*."""
    builder = BUILDERS.get(cfg.target_type)
    if builder is None:
        raise RuntimeError(f"No builder for type: {cfg.target_type}")

    out_dir = os.path.dirname(cfg.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    return builder(cfg)


__all__ = [
    "BUILDERS",
    "_NSIS_TEMPLATE",
    "_appimage_arch",
    "_flatpak_arch",
    "_host_arch",
    "_sanitise_name",
    "build",
    "build_app",
    "build_app_in_dmg",
    "build_appimage",
    "build_deb",
    "build_dmg",
    "build_flatpak",
    "build_nsis",
    "build_rpm",
    "build_snap",
    "build_tar_gz",
    "build_zip",
]
