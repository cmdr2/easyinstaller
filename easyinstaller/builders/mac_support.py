"""Shared macOS packaging and notarization helpers."""

from __future__ import annotations

import os
import plistlib
import shutil
import stat
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath

from ..config import Config
from .common import _require, _run


def _escape_applescript_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _mac_application_sign_identity(cfg: Config) -> str:
    return f"Developer ID Application: {cfg.mac_notary_team_name} ({cfg.mac_notary_team_id})"


def _mac_installer_sign_identity(cfg: Config) -> str:
    return f"Developer ID Installer: {cfg.mac_notary_team_name} ({cfg.mac_notary_team_id})"


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
    _run(
        [
            "codesign",
            "--force",
            "--sign",
            _mac_application_sign_identity(cfg),
            "--timestamp",
            "--options",
            "runtime",
            path,
        ]
    )


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


def _summarise_command_failure(exc: subprocess.CalledProcessError) -> str:
    command = " ".join(str(arg) for arg in (exc.cmd or [])) or "command"
    output = exc.stderr or exc.stdout or ""
    summary = ""
    if output:
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if lines:
            summary = lines[-1]
    if summary:
        return f"{command} failed with exit code {exc.returncode}: {summary}"
    return f"{command} failed with exit code {exc.returncode}"


def _run_quiet(args: list[str]) -> None:
    try:
        _run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(_summarise_command_failure(exc)) from exc


def _prepare_mac_source(cfg: Config, prefix: str) -> str:
    temp_root = tempfile.mkdtemp(prefix=prefix)
    shutil.copytree(cfg.source, temp_root, dirs_exist_ok=True)

    if cfg.mac_notarize:
        _require("codesign")
        _require("xcrun")
        for path in _iter_signable_paths(temp_root):
            _codesign_path(path, cfg)

    return temp_root


def _submit_for_notarization(target: str, cfg: Config) -> None:
    _run_quiet(["xcrun", "notarytool", "submit", target, "--wait", *_notarytool_auth_args(cfg)])


def _staple_ticket(target: str) -> None:
    _run_quiet(["xcrun", "stapler", "staple", target])


def _finalize_mac_output(cfg: Config, output_file: str) -> None:
    if cfg.target_os != "mac" or not cfg.mac_notarize:
        return
    _submit_for_notarization(output_file, cfg)
    if cfg.target_type in {"app", "dmg", "app-in-dmg", "pkg", "app-in-pkg"}:
        _staple_ticket(output_file)


def _write_product_requirements() -> str:
    handle = tempfile.NamedTemporaryFile(prefix="easyinstaller-product-", suffix=".plist", delete=False)
    try:
        with handle:
            plistlib.dump({"home": True}, handle)
    except Exception:
        os.unlink(handle.name)
        raise
    return handle.name


def _enable_home_install_domain(distribution_path: str) -> None:
    tree = ET.parse(distribution_path)
    root = tree.getroot()

    domains = root.find("domains")
    if domains is None:
        domains = ET.Element("domains")
        children = list(root)
        insert_at = 0
        for index, child in enumerate(children):
            if child.tag != "pkg-ref":
                insert_at = index
                break
            insert_at = index + 1
        root.insert(insert_at, domains)

    domains.set("enable_anywhere", "false")
    domains.set("enable_currentUserHome", "true")
    domains.set("enable_localSystem", "true")

    tree.write(distribution_path, encoding="utf-8", xml_declaration=True)


def _build_product_archive(component_pkg: str, output_file: str, cfg: Config | None = None) -> str:
    _require("productbuild")
    if os.path.exists(output_file):
        os.remove(output_file)

    requirements_path = _write_product_requirements()
    distribution_path = os.path.join(os.path.dirname(component_pkg), "Distribution")
    try:
        _run(
            [
                "productbuild",
                "--synthesize",
                "--product",
                requirements_path,
                "--package",
                component_pkg,
                distribution_path,
            ]
        )
        _enable_home_install_domain(distribution_path)

        args = [
            "productbuild",
            "--distribution",
            distribution_path,
            "--package-path",
            os.path.dirname(component_pkg),
        ]
        if cfg is not None and cfg.mac_notarize:
            args.extend(["--sign", _mac_installer_sign_identity(cfg)])
        args.append(output_file)
        _run(args)
    finally:
        os.unlink(requirements_path)
        if os.path.exists(distribution_path):
            os.unlink(distribution_path)

    return output_file


def _create_dmg_image(source: str, output_file: str, volume_name: str) -> str:
    _require("hdiutil")
    _run(["hdiutil", "create", "-volname", volume_name, "-srcfolder", source, "-ov", "-format", "UDZO", output_file])
    return output_file


def _style_app_dmg_window(mount_dir: str, app_item_name: str) -> None:
    _require("osascript")
    mount_dir = os.path.abspath(mount_dir)
    script_lines = [
        'tell application "Finder"',
        'set diskFolder to (POSIX file "' + _escape_applescript_string(mount_dir) + '" as alias)',
        "open diskFolder",
        "set dmgWindow to container window of diskFolder",
        "set current view of dmgWindow to icon view",
        "set toolbar visible of dmgWindow to false",
        "set statusbar visible of dmgWindow to false",
        "set bounds of dmgWindow to {120, 120, 760, 480}",
        "set opts to icon view options of dmgWindow",
        "set arrangement of opts to not arranged",
        "set icon size of opts to 128",
        'set position of item "' + _escape_applescript_string(app_item_name) + '" of diskFolder to {170, 180}',
        'set position of item "Applications" of diskFolder to {470, 180}',
        "close dmgWindow",
        "open diskFolder",
        "update diskFolder without registering applications",
        "delay 1",
        "end tell",
    ]
    args = ["osascript"]
    for line in script_lines:
        args.extend(["-e", line])
    _run(args, cwd=mount_dir)


def _create_styled_app_dmg_image(source: str, output_file: str, volume_name: str, app_item_name: str) -> str:
    _require("hdiutil")

    temp_image = tempfile.NamedTemporaryFile(prefix="easyinstaller-app-dmg-", suffix=".dmg", delete=False)
    mount_dir = tempfile.mkdtemp(prefix="easyinstaller-app-dmg-mount-")
    temp_image.close()
    try:
        _run(
            [
                "hdiutil",
                "create",
                "-volname",
                volume_name,
                "-srcfolder",
                source,
                "-ov",
                "-format",
                "UDRW",
                temp_image.name,
            ]
        )
        _run(["hdiutil", "attach", temp_image.name, "-readwrite", "-noverify", "-noautoopen", "-mountpoint", mount_dir])
        try:
            _style_app_dmg_window(mount_dir, app_item_name)
        finally:
            _run(["hdiutil", "detach", mount_dir])

        if os.path.exists(output_file):
            os.remove(output_file)
        _run(["hdiutil", "convert", temp_image.name, "-ov", "-format", "UDZO", "-o", output_file])
    finally:
        if os.path.exists(temp_image.name):
            os.unlink(temp_image.name)
        shutil.rmtree(mount_dir, ignore_errors=True)

    return output_file


def _create_applications_alias(destination_dir: str, alias_name: str = "Applications") -> str:
    _require("osascript")
    alias_path = os.path.join(destination_dir, alias_name)
    if os.path.lexists(alias_path):
        if os.path.isdir(alias_path) and not os.path.islink(alias_path):
            shutil.rmtree(alias_path)
        else:
            os.unlink(alias_path)

    destination_dir = os.path.abspath(destination_dir)
    script_lines = [
        'tell application "Finder"',
        (
            'make new alias file at POSIX file "'
            + _escape_applescript_string(destination_dir)
            + '" to POSIX file "/Applications" '
            + 'with properties {name:"'
            + _escape_applescript_string(alias_name)
            + '"}'
        ),
        "end tell",
    ]
    args = ["osascript"]
    for line in script_lines:
        args.extend(["-e", line])
    _run(args)
    return alias_path


def _create_pkg_from_root(
    source: str,
    output_file: str,
    install_location: str,
    identifier: str,
    version: str,
    cfg: Config | None = None,
) -> str:
    _require("pkgbuild")
    component_pkg = os.path.join(os.path.dirname(output_file), f"{identifier}.component.pkg")
    try:
        args = [
            "pkgbuild",
            "--root",
            source,
            "--identifier",
            identifier,
            "--version",
            version,
            "--install-location",
            install_location,
            component_pkg,
        ]
        _run(args)
        return _build_product_archive(component_pkg, output_file, cfg)
    finally:
        if os.path.exists(component_pkg):
            os.unlink(component_pkg)


def _create_pkg_from_component(
    component_path: str,
    output_file: str,
    install_location: str,
    identifier: str,
    version: str,
    cfg: Config | None = None,
) -> str:
    _require("pkgbuild")
    component_pkg = os.path.join(os.path.dirname(output_file), f"{identifier}.component.pkg")
    try:
        args = [
            "pkgbuild",
            "--component",
            component_path,
            "--identifier",
            identifier,
            "--version",
            version,
            "--install-location",
            install_location,
            component_pkg,
        ]
        _run(args)
        return _build_product_archive(component_pkg, output_file, cfg)
    finally:
        if os.path.exists(component_pkg):
            os.unlink(component_pkg)


def _bundle_identifier(app_name: str, suffix: str = ".app") -> str:
    import re

    return "com." + re.sub(r"[^a-z0-9]", "", app_name.lower()) + suffix


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
