"""Builder functions — one per target type.

Every public ``build_*`` function accepts a :class:`~easy_installer.config.Config`
and returns the path to the created artefact.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import tempfile
import zipfile

from .config import Config

log = logging.getLogger("easy-installer")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _require(cmd: str) -> str:
    """Return the absolute path of *cmd*, or raise."""
    path = shutil.which(cmd)
    if path is None:
        raise RuntimeError(f"'{cmd}' is required but not found in PATH. Please install it.")
    return path


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a subprocess, raising on failure."""
    log.debug("Running: %s", " ".join(args))
    return subprocess.run(args, check=True, **kwargs)


def _deb_arch(arch: str) -> str:
    return {"x86_64": "amd64", "arm64": "arm64", "i386": "i386", "armhf": "armhf"}[arch]


def _rpm_arch(arch: str) -> str:
    return {"x86_64": "x86_64", "arm64": "aarch64", "i386": "i686", "armhf": "armv7hl"}[arch]


def _appimage_arch(arch: str) -> str:
    return {"x86_64": "x86_64", "arm64": "aarch64", "i386": "i686", "armhf": "armhf"}[arch]


def _host_arch() -> str:
    """Return the appimagetool arch string for the current host machine."""
    machine = platform.machine().lower()
    mapping = {
        "x86_64": "x86_64", "amd64": "x86_64",
        "aarch64": "aarch64", "arm64": "aarch64",
        "i386": "i686", "i686": "i686", "x86": "i686",
        "armv7l": "armhf",
    }
    result = mapping.get(machine)
    if result is None:
        log.warning("Unknown host architecture '%s'; using as-is for appimagetool download", machine)
        return machine
    return result


def _flatpak_arch(arch: str) -> str:
    return {"x86_64": "x86_64", "arm64": "aarch64", "i386": "i386", "armhf": "arm"}[arch]


def _sanitise_name(name: str) -> str:
    """Lower-case, replace non-alphanumeric with hyphens, collapse multiples."""
    import re
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


# ── Archive builders ─────────────────────────────────────────────────────────

def build_zip(cfg: Config) -> str:
    output_file = cfg.output + ".zip"
    log.info("Creating zip archive: %s", output_file)
    base_name = os.path.basename(cfg.source)
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(cfg.source):
            # Add empty directories explicitly
            if not filenames and not dirnames:
                arc_dir = os.path.join(base_name, os.path.relpath(dirpath, cfg.source)) + "/"
                zf.writestr(zipfile.ZipInfo(arc_dir), "")
            for fn in filenames:
                abs_path = os.path.join(dirpath, fn)
                arc_name = os.path.join(base_name, os.path.relpath(abs_path, cfg.source))
                zf.write(abs_path, arc_name)
    log.info("Created: %s", output_file)
    return output_file


def build_tar_gz(cfg: Config) -> str:
    import tarfile
    output_file = cfg.output + ".tar.gz"
    log.info("Creating tar.gz archive: %s", output_file)
    with tarfile.open(output_file, "w:gz") as tf:
        tf.add(cfg.source, arcname=os.path.basename(cfg.source))
    log.info("Created: %s", output_file)
    return output_file


# ── Windows ──────────────────────────────────────────────────────────────────

def build_nsis(cfg: Config) -> str:
    _require("makensis")
    output_file = cfg.output + ".exe"
    log.info("Creating NSIS installer: %s", output_file)

    # Gather file install/uninstall lines and track subdirectories
    install_lines: list[str] = []
    uninstall_lines: list[str] = []
    subdirs: set[str] = set()
    for dirpath, _dirs, filenames in os.walk(cfg.source):
        rel_dir = os.path.relpath(dirpath, cfg.source)
        if rel_dir != ".":
            subdirs.add(rel_dir.replace("/", "\\"))
        for fn in filenames:
            abs_path = os.path.join(dirpath, fn)
            rel = os.path.relpath(abs_path, cfg.source)
            win_rel = rel.replace("/", "\\")
            win_dir = os.path.dirname(win_rel) or "."
            out_dir = "" if win_dir == "." else ("\\" + win_dir)
            install_lines.append(f'  SetOutPath "$INSTDIR{out_dir}"')
            install_lines.append(f'  File "{abs_path}"')
            uninstall_lines.append(f'  Delete "$INSTDIR\\{win_rel}"')

    # Remove subdirectories deepest-first so parent dirs are empty when removed
    for d in sorted(subdirs, key=lambda p: p.count("\\"), reverse=True):
        uninstall_lines.append(f'  RMDir "$INSTDIR\\{d}"')

    nsi = _NSIS_TEMPLATE.format(
        app_name=cfg.app_name,
        app_version=cfg.app_version,
        output_file=output_file,
        install_files="\n".join(install_lines),
        uninstall_files="\n".join(uninstall_lines),
    )

    fd, nsi_path = tempfile.mkstemp(suffix=".nsi", prefix="easy-installer-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(nsi)
        _run(["makensis", nsi_path])
    finally:
        os.unlink(nsi_path)

    log.info("Created: %s", output_file)
    return output_file


_NSIS_TEMPLATE = r"""!include "MUI2.nsh"

Name "{app_name}"
OutFile "{output_file}"
InstallDir "$PROGRAMFILES\{app_name}"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
{install_files}
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\{app_name}"
  CreateShortcut "$SMPROGRAMS\{app_name}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}" "DisplayName" "{app_name}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}" "DisplayVersion" "{app_version}"
SectionEnd

Section "Uninstall"
{uninstall_files}
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\{app_name}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\{app_name}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}"
SectionEnd
"""


# ── Linux: deb ───────────────────────────────────────────────────────────────

def build_deb(cfg: Config) -> str:
    _require("dpkg-deb")
    output_file = cfg.output + ".deb"
    log.info("Creating deb package: %s", output_file)

    deb_root = tempfile.mkdtemp(prefix="easy-installer-deb-")
    try:
        pkg_name = _sanitise_name(cfg.app_name)
        install_prefix = f"opt/{pkg_name}"
        dest = os.path.join(deb_root, install_prefix)
        shutil.copytree(cfg.source, dest, dirs_exist_ok=True)

        debian_dir = os.path.join(deb_root, "DEBIAN")
        os.makedirs(debian_dir, exist_ok=True)

        with open(os.path.join(debian_dir, "control"), "w") as f:
            f.write(
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
            os.symlink(
                f"/{install_prefix}/{cfg.app_exec}",
                os.path.join(usr_bin, cfg.app_exec),
            )

        _run(["dpkg-deb", "--build", "--root-owner-group", deb_root, output_file])
    finally:
        shutil.rmtree(deb_root, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file


# ── Linux: rpm ───────────────────────────────────────────────────────────────

def build_rpm(cfg: Config) -> str:
    _require("rpmbuild")
    output_file = cfg.output + ".rpm"
    log.info("Creating rpm package: %s", output_file)

    rpm_root = tempfile.mkdtemp(prefix="easy-installer-rpm-")
    try:
        for d in ("BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS", "BUILDROOT"):
            os.makedirs(os.path.join(rpm_root, d))

        sanitised = _sanitise_name(cfg.app_name)
        install_prefix = f"opt/{sanitised}"

        # Create source tarball
        src_staging = tempfile.mkdtemp(prefix="easy-installer-rpmsrc-")
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
        with open(spec_path, "w") as f:
            f.write(
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

        _run([
            "rpmbuild",
            "--define", f"_topdir {rpm_root}",
            "--target", _rpm_arch(cfg.arch),
            "-bb", spec_path,
        ])

        # Find built RPM
        rpms_dir = os.path.join(rpm_root, "RPMS")
        built = None
        for dirpath, _dirs, files in os.walk(rpms_dir):
            for fn in files:
                if fn.endswith(".rpm"):
                    built = os.path.join(dirpath, fn)
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


# ── Linux: AppImage ──────────────────────────────────────────────────────────

def build_appimage(cfg: Config) -> str:
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for AppImage")

    output_file = cfg.output + ".AppImage"
    log.info("Creating AppImage: %s", output_file)

    appdir = tempfile.mkdtemp(prefix="easy-installer-appimage-")
    try:
        usr_bin = os.path.join(appdir, "usr", "bin")
        os.makedirs(usr_bin)
        shutil.copytree(cfg.source, usr_bin, dirs_exist_ok=True)

        desktop_dir = os.path.join(appdir, "usr", "share", "applications")
        icon_dir = os.path.join(appdir, "usr", "share", "icons", "hicolor", "256x256", "apps")
        os.makedirs(desktop_dir)
        os.makedirs(icon_dir)

        desktop = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={cfg.app_name}\n"
            f"Exec={cfg.app_exec}\n"
            f"Icon={cfg.app_name}\n"
            f"Categories={cfg.app_category};\n"
        )
        with open(os.path.join(appdir, f"{cfg.app_name}.desktop"), "w") as f:
            f.write(desktop)
        with open(os.path.join(desktop_dir, f"{cfg.app_name}.desktop"), "w") as f:
            f.write(desktop)

        # Icon
        if cfg.app_icon and os.path.isfile(cfg.app_icon):
            shutil.copy2(cfg.app_icon, os.path.join(appdir, f"{cfg.app_name}.png"))
            shutil.copy2(cfg.app_icon, os.path.join(icon_dir, f"{cfg.app_name}.png"))
        else:
            # Minimal valid 1×1 PNG so appimagetool doesn't fail
            import base64
            pixel = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
                "2mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            )
            for p in (
                os.path.join(appdir, f"{cfg.app_name}.png"),
                os.path.join(icon_dir, f"{cfg.app_name}.png"),
            ):
                with open(p, "wb") as f:
                    f.write(pixel)

        # AppRun
        apprun = os.path.join(appdir, "AppRun")
        with open(apprun, "w") as f:
            f.write(
                '#!/bin/bash\n'
                'SELF="$(readlink -f "$0")"\n'
                'HERE="$(dirname "$SELF")"\n'
                'export PATH="${HERE}/usr/bin:${PATH}"\n'
                'export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"\n'
                f'exec "${{HERE}}/usr/bin/{cfg.app_exec}" "$@"\n'
            )
        os.chmod(apprun, 0o755)

        # Locate or download appimagetool (must be for the HOST architecture)
        appimagetool = shutil.which("appimagetool") or "/tmp/appimagetool"
        if not os.path.isfile(appimagetool) or not os.access(appimagetool, os.X_OK):
            host_arch = _host_arch()
            url = (
                "https://github.com/AppImage/appimagetool/releases/"
                f"download/continuous/appimagetool-{host_arch}.AppImage"
            )
            log.info("Downloading appimagetool from %s", url)
            import urllib.request
            urllib.request.urlretrieve(url, appimagetool)
            os.chmod(appimagetool, 0o755)

        env = {**os.environ, "ARCH": _appimage_arch(cfg.arch)}
        try:
            _run([appimagetool, appdir, output_file], env=env)
        except subprocess.CalledProcessError:
            _run([appimagetool, "--appimage-extract-and-run", appdir, output_file], env=env)
    finally:
        shutil.rmtree(appdir, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file


# ── Linux: Flatpak ───────────────────────────────────────────────────────────

def build_flatpak(cfg: Config) -> str:
    _require("flatpak")
    _require("flatpak-builder")
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for Flatpak")

    output_file = cfg.output + ".flatpak"
    log.info("Creating Flatpak: %s", output_file)

    import json
    import re
    sanitised_id = "com." + re.sub(r"[^a-z0-9]", "", cfg.app_name.lower()) + ".app"

    build_dir = tempfile.mkdtemp(prefix="easy-installer-flatpak-")
    try:
        src_copy = os.path.join(build_dir, "source")
        shutil.copytree(cfg.source, src_copy)

        # Ensure runtime is available
        subprocess.run(
            ["flatpak", "remote-add", "--user", "--if-not-exists",
             "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"],
            check=False,
        )
        subprocess.run(
            ["flatpak", "install", "--user", "-y",
             "flathub", "org.freedesktop.Platform//23.08", "org.freedesktop.Sdk//23.08"],
            check=False,
        )

        manifest = {
            "app-id": sanitised_id,
            "runtime": "org.freedesktop.Platform",
            "runtime-version": "23.08",
            "sdk": "org.freedesktop.Sdk",
            "command": cfg.app_exec,
            "modules": [{
                "name": _sanitise_name(cfg.app_name),
                "buildsystem": "simple",
                "build-commands": [
                    "mkdir -p /app/bin",
                    "cp -a . /app/bin/",
                ],
                "sources": [{"type": "dir", "path": "source"}],
            }],
        }
        manifest_path = os.path.join(build_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        fp_arch = _flatpak_arch(cfg.arch)
        _run(["flatpak-builder", "--user", "--force-clean",
              "--arch", fp_arch,
              os.path.join(build_dir, "build"), manifest_path])
        _run(["flatpak", "build-export",
              "--arch", fp_arch,
              os.path.join(build_dir, "repo"),
              os.path.join(build_dir, "build")])
        _run(["flatpak", "build-bundle",
              "--arch", fp_arch,
              os.path.join(build_dir, "repo"),
              output_file, sanitised_id])
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file


# ── Linux: Snap ──────────────────────────────────────────────────────────────

def build_snap(cfg: Config) -> str:
    _require("snapcraft")
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for Snap")

    output_file = cfg.output + ".snap"
    log.info("Creating Snap: %s", output_file)

    sanitised = _sanitise_name(cfg.app_name)
    snap_dir = tempfile.mkdtemp(prefix="easy-installer-snap-")
    try:
        shutil.copytree(cfg.source, os.path.join(snap_dir, "source"))
        snap_meta = os.path.join(snap_dir, "snap")
        os.makedirs(snap_meta)

        with open(os.path.join(snap_meta, "snapcraft.yaml"), "w") as f:
            f.write(
                f"name: {sanitised}\n"
                f"version: '{cfg.app_version}'\n"
                f"summary: {cfg.app_description}\n"
                f"description: |\n"
                f"  {cfg.app_description}\n"
                f"base: core22\n"
                f"grade: stable\n"
                f"confinement: strict\n"
                f"\n"
                f"parts:\n"
                f"  {sanitised}:\n"
                f"    plugin: dump\n"
                f"    source: source/\n"
                f"\n"
                f"apps:\n"
                f"  {sanitised}:\n"
                f"    command: {cfg.app_exec}\n"
            )

        _run(["snapcraft", "--destructive-mode"], cwd=snap_dir)

        # Find built snap
        built = None
        for fn in os.listdir(snap_dir):
            if fn.endswith(".snap"):
                built = os.path.join(snap_dir, fn)
                break
        if not built:
            raise RuntimeError("Snap build failed — no output found")
        shutil.copy2(built, output_file)
    finally:
        shutil.rmtree(snap_dir, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file


# ── Mac: DMG ─────────────────────────────────────────────────────────────────

def build_dmg(cfg: Config) -> str:
    _require("hdiutil")
    output_file = cfg.output + ".dmg"
    log.info("Creating DMG: %s", output_file)

    staging = tempfile.mkdtemp(prefix="easy-installer-dmg-")
    try:
        shutil.copytree(cfg.source, staging, dirs_exist_ok=True)
        _run([
            "hdiutil", "create",
            "-volname", cfg.app_name,
            "-srcfolder", staging,
            "-ov", "-format", "UDZO",
            output_file,
        ])
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file


# ── Mac: .app bundle ────────────────────────────────────────────────────────

def build_app(cfg: Config) -> str:
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for .app bundles")

    output_file = cfg.output + ".app"
    log.info("Creating .app bundle: %s", output_file)

    import re
    bundle_id = "com." + re.sub(r"[^a-z0-9]", "", cfg.app_name.lower()) + ".app"

    staging = tempfile.mkdtemp(prefix="easy-installer-app-")
    try:
        app_root = os.path.join(staging, os.path.basename(output_file))
        contents = os.path.join(app_root, "Contents")
        macos = os.path.join(contents, "MacOS")
        resources = os.path.join(contents, "Resources")
        os.makedirs(macos)
        os.makedirs(resources)

        shutil.copytree(cfg.source, resources, dirs_exist_ok=True)

        # Launcher script
        launcher = os.path.join(macos, cfg.app_exec)
        with open(launcher, "w") as f:
            f.write(
                '#!/bin/bash\n'
                'DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"\n'
                f'exec "${{DIR}}/{cfg.app_exec}" "$@"\n'
            )
        os.chmod(launcher, 0o755)

        # Info.plist
        icon_entry = ""
        if cfg.app_icon and os.path.isfile(cfg.app_icon):
            icon_name = os.path.basename(cfg.app_icon)
            icon_entry = (
                '    <key>CFBundleIconFile</key>\n'
                f'    <string>{icon_name}</string>\n'
            )
        with open(os.path.join(contents, "Info.plist"), "w") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
                ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                '<plist version="1.0">\n'
                '<dict>\n'
                '    <key>CFBundleExecutable</key>\n'
                f'    <string>{cfg.app_exec}</string>\n'
                '    <key>CFBundleIdentifier</key>\n'
                f'    <string>{bundle_id}</string>\n'
                '    <key>CFBundleName</key>\n'
                f'    <string>{cfg.app_name}</string>\n'
                '    <key>CFBundleVersion</key>\n'
                f'    <string>{cfg.app_version}</string>\n'
                '    <key>CFBundleShortVersionString</key>\n'
                f'    <string>{cfg.app_version}</string>\n'
                '    <key>CFBundlePackageType</key>\n'
                '    <string>APPL</string>\n'
                f'{icon_entry}'
                '</dict>\n'
                '</plist>\n'
            )

        if cfg.app_icon and os.path.isfile(cfg.app_icon):
            shutil.copy2(cfg.app_icon, os.path.join(resources, os.path.basename(cfg.app_icon)))

        # Move to final location (remove existing if present)
        if os.path.exists(output_file):
            shutil.rmtree(output_file)
        shutil.copytree(app_root, output_file)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file


# ── Dispatcher ───────────────────────────────────────────────────────────────

from typing import Callable

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
}


def build(cfg: Config) -> str:
    """Dispatch to the appropriate builder based on *cfg.target_type*."""
    builder = BUILDERS.get(cfg.target_type)
    if builder is None:
        raise RuntimeError(f"No builder for type: {cfg.target_type}")

    # Ensure the output's parent directory exists
    out_dir = os.path.dirname(cfg.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    return builder(cfg)
