"""RPM builder."""

from __future__ import annotations

import os
import shutil
import tempfile

from ..config import Config
from .common import _require, _rpm_arch, _run, _sanitise_name, log


def build_rpm(cfg: Config) -> str:
    _require("rpmbuild")
    output_file = cfg.output + ".rpm"
    log.info("Creating rpm package: %s", output_file)

    rpm_root = tempfile.mkdtemp(prefix="easyinstaller-rpm-")
    try:
        for directory in ("BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS", "BUILDROOT"):
            os.makedirs(os.path.join(rpm_root, directory))

        sanitised = _sanitise_name(cfg.app_name)
        install_prefix = f"opt/{sanitised}"

        src_staging = tempfile.mkdtemp(prefix="easyinstaller-rpmsrc-")
        try:
            staging_inner = os.path.join(src_staging, f"{sanitised}-{cfg.app_version}")
            shutil.copytree(cfg.source, staging_inner, dirs_exist_ok=True)
            import tarfile

            tarball = os.path.join(rpm_root, "SOURCES", f"{sanitised}-{cfg.app_version}.tar.gz")
            with tarfile.open(tarball, "w:gz") as tf:
                tf.add(staging_inner, arcname=f"{sanitised}-{cfg.app_version}")
        finally:
            shutil.rmtree(src_staging, ignore_errors=True)

        spec_path = os.path.join(rpm_root, "SPECS", f"{sanitised}.spec")
        with open(spec_path, "w") as handle:
            handle.write(
                f"Name:           {sanitised}\n"
                f"Version:        {cfg.app_version}\n"
                f"Release:        1\n"
                f"Summary:        {cfg.app_description}\n"
                f"License:        Proprietary\n"
                f"Source0:        {sanitised}-{cfg.app_version}.tar.gz\n"
                f"\n"
                f"%description\n"
                f"{cfg.app_description}\n"
                f"\n"
                f"%prep\n"
                f"%setup -q -n {sanitised}-{cfg.app_version}\n"
                f"\n"
                f"%install\n"
                f"mkdir -p %{{buildroot}}/{install_prefix}\n"
                f"cp -a . %{{buildroot}}/{install_prefix}/\n"
                f"\n"
                f"%files\n"
                f"/{install_prefix}\n"
            )

        _run(["rpmbuild", "--define", f"_topdir {rpm_root}", "--target", _rpm_arch(cfg.arch), "-bb", spec_path])

        built = None
        for dirpath, _dirs, files in os.walk(os.path.join(rpm_root, "RPMS")):
            for filename in files:
                if filename.endswith(".rpm"):
                    built = os.path.join(dirpath, filename)
                    break
            if built:
                break
        if not built:
            raise RuntimeError("RPM build failed — no output found")
        shutil.copy2(built, output_file)
    finally:
        shutil.rmtree(rpm_root, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file