"""deb builder."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import PurePosixPath

from ..config import Config
from .common import _deb_arch, _require, _run, _sanitise_name, log


def build_deb(cfg: Config) -> str:
    _require("dpkg-deb")
    output_file = cfg.output + ".deb"
    log.info("Creating deb package: %s", output_file)

    deb_root = tempfile.mkdtemp(prefix="easyinstaller-deb-")
    try:
        pkg_name = _sanitise_name(cfg.app_name)
        install_prefix = f"opt/{pkg_name}"
        dest = os.path.join(deb_root, install_prefix)
        shutil.copytree(cfg.source, dest, dirs_exist_ok=True)

        debian_dir = os.path.join(deb_root, "DEBIAN")
        os.makedirs(debian_dir, exist_ok=True)

        with open(os.path.join(debian_dir, "control"), "w") as handle:
            handle.write(
                f"Package: {pkg_name}\n"
                f"Version: {cfg.app_version}\n"
                f"Architecture: {_deb_arch(cfg.arch)}\n"
                f"Maintainer: {cfg.app_maintainer}\n"
                f"Description: {cfg.app_description}\n"
                f"Section: {cfg.app_category}\n"
                f"Priority: optional\n"
            )

        if cfg.app_exec:
            usr_bin = os.path.join(deb_root, "usr", "bin")
            os.makedirs(usr_bin, exist_ok=True)
            os.symlink(f"/{install_prefix}/{cfg.app_exec}", os.path.join(usr_bin, PurePosixPath(cfg.app_exec).name))

        _run(["dpkg-deb", "--build", "--root-owner-group", deb_root, output_file])
    finally:
        shutil.rmtree(deb_root, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file
