"""Shared macOS packaging and notarization helpers."""

from __future__ import annotations

import os
import plistlib
import shutil
import stat
import tempfile
from pathlib import PurePosixPath

from ..config import Config
from .common import _require, _run


def _is_signable_file(path: str) -> bool:
    if os.path.isdir(path) or os.path.islink(path):
        return False
    if path.endswith(".dylib"):
        return True
    mode = os.stat(path, follow_symlinks=False).st_mode
    if bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)):
        return True
    _stem, suffix = os.path.splitext(path)
    return not suffix and os.access(path, os.X_OK)


def _iter_signable_paths(root: str) -> list[str]:
    candidates: list[str] = []
    for dirpath, _dirs, filenames in os.walk(root):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            if _is_signable_file(path):
                candidates.append(path)
    return sorted(candidates, key=lambda path: (path.count(os.sep), path))


def _codesign_path(path: str, cfg: Config) -> None:
    _run(["codesign", "--force", "--sign", cfg.mac_sign_identity, "--timestamp", "--options", "runtime", path])


def _notarytool_auth_args(cfg: Config) -> list[str]:
    if cfg.mac_notary_keychain_profile:
        return ["--keychain-profile", cfg.mac_notary_keychain_profile]
    return [
        "--apple-id",
        cfg.mac_notary_apple_id,
        "--team-id",
        cfg.mac_notary_team_id,
        "--password",
        cfg.mac_notary_password,
    ]


def _prepare_mac_source(cfg: Config, prefix: str) -> tuple[str, str]:
    temp_root = tempfile.mkdtemp(prefix=prefix)
    source_copy = os.path.join(temp_root, os.path.basename(cfg.source))
    shutil.copytree(cfg.source, source_copy)

    if cfg.mac_notarize:
        _require("codesign")
        _require("xcrun")
        for path in _iter_signable_paths(source_copy):
            _codesign_path(path, cfg)

    return temp_root, source_copy


def _submit_for_notarization(target: str, cfg: Config) -> None:
    _run(["xcrun", "notarytool", "submit", target, "--wait", *_notarytool_auth_args(cfg)])


def _staple_ticket(target: str) -> None:
    _run(["xcrun", "stapler", "staple", "-v", target])


def _finalize_mac_output(cfg: Config, output_file: str) -> None:
    if cfg.target_os != "mac" or not cfg.mac_notarize:
        return
    _submit_for_notarization(output_file, cfg)
    if cfg.target_type in {"app", "dmg", "app-in-dmg"}:
        _staple_ticket(output_file)


def _create_dmg_image(source: str, output_file: str, volume_name: str) -> str:
    _require("hdiutil")
    _run(["hdiutil", "create", "-volname", volume_name, "-srcfolder", source, "-ov", "-format", "UDZO", output_file])
    return output_file


def _bundle_identifier(app_name: str) -> str:
    import re

    return "com." + re.sub(r"[^a-z0-9]", "", app_name.lower()) + ".app"


def _create_app_bundle(cfg: Config, source_dir: str, output_file: str) -> str:
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for .app bundles")

    staging = tempfile.mkdtemp(prefix="easyinstaller-app-")
    try:
        launcher_name = PurePosixPath(cfg.app_exec).name
        app_root = os.path.join(staging, os.path.basename(output_file))
        contents = os.path.join(app_root, "Contents")
        macos = os.path.join(contents, "MacOS")
        resources = os.path.join(contents, "Resources")
        os.makedirs(macos)
        os.makedirs(resources)

        shutil.copytree(source_dir, resources, dirs_exist_ok=True)

        launcher = os.path.join(macos, launcher_name)
        with open(launcher, "w") as handle:
            handle.write(
                "#!/bin/bash\n"
                'DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"\n'
                f'exec "${{DIR}}/{cfg.app_exec}" "$@"\n'
            )
        os.chmod(launcher, 0o755)

        plist_data = {
            "CFBundleExecutable": launcher_name,
            "CFBundleIdentifier": _bundle_identifier(cfg.app_name),
            "CFBundleName": cfg.app_name,
            "CFBundleVersion": cfg.app_version,
            "CFBundleShortVersionString": cfg.app_version,
            "CFBundlePackageType": "APPL",
        }
        if cfg.app_icon and os.path.isfile(cfg.app_icon):
            plist_data["CFBundleIconFile"] = os.path.basename(cfg.app_icon)
        with open(os.path.join(contents, "Info.plist"), "wb") as handle:
            plistlib.dump(plist_data, handle)

        if cfg.app_icon and os.path.isfile(cfg.app_icon):
            shutil.copy2(cfg.app_icon, os.path.join(resources, os.path.basename(cfg.app_icon)))

        if cfg.mac_notarize:
            _codesign_path(launcher, cfg)
            _codesign_path(app_root, cfg)

        if os.path.exists(output_file):
            shutil.rmtree(output_file)
        shutil.copytree(app_root, output_file)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    return output_file
