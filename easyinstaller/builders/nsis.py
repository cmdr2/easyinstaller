"""NSIS builder."""

from __future__ import annotations

import os
import tempfile

from ..config import Config
from .common import _require, _run, log


def _escape_nsis_string(value: str) -> str:
    return value.replace("$", "$$").replace('"', '$\\"').replace("\r", " ").replace("\n", " ")


def _normalise_nsis_component(value: str) -> str:
    normalised = value.replace("\\", "-").replace("/", "-").replace('"', "'")
    normalised = " ".join(normalised.split())
    return normalised or "Application"


def build_nsis(cfg: Config) -> str:
    _require("makensis")
    output_file = cfg.output + ".exe"
    log.info("Creating NSIS installer: %s", output_file)

    display_name = _escape_nsis_string(cfg.app_name)
    install_name = _escape_nsis_string(_normalise_nsis_component(cfg.app_name))
    display_version = _escape_nsis_string(cfg.app_version)

    install_lines: list[str] = []
    uninstall_lines: list[str] = []
    subdirs: set[str] = set()
    for dirpath, _dirs, filenames in os.walk(cfg.source):
        rel_dir = os.path.relpath(dirpath, cfg.source)
        if rel_dir != ".":
            subdirs.add(rel_dir.replace("/", "\\"))
        for filename in filenames:
            abs_path = os.path.join(dirpath, filename)
            rel = os.path.relpath(abs_path, cfg.source)
            win_rel = rel.replace("/", "\\")
            win_dir = os.path.dirname(win_rel) or "."
            out_dir = "" if win_dir == "." else ("\\" + win_dir)
            install_lines.append(f'  SetOutPath "$INSTDIR{out_dir}"')
            install_lines.append(f'  File "{abs_path}"')
            uninstall_lines.append(f'  Delete "$INSTDIR\\{win_rel}"')

    for subdir in sorted(subdirs, key=lambda path: path.count("\\"), reverse=True):
        uninstall_lines.append(f'  RMDir "$INSTDIR\\{subdir}"')

    nsi = _NSIS_TEMPLATE.format(
        app_name=display_name,
        install_name=install_name,
        app_version=display_version,
        output_file=output_file,
        install_files="\n".join(install_lines),
        uninstall_files="\n".join(uninstall_lines),
    )

    fd, nsi_path = tempfile.mkstemp(suffix=".nsi", prefix="easyinstaller-")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(nsi)
        _run(["makensis", nsi_path])
    finally:
        os.unlink(nsi_path)

    log.info("Created: %s", output_file)
    return output_file


_NSIS_TEMPLATE = r"""!include "MUI2.nsh"

Name "{app_name}"
OutFile "{output_file}"
InstallDir "$PROGRAMFILES\{install_name}"
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
    CreateDirectory "$SMPROGRAMS\{install_name}"
    CreateShortcut "$SMPROGRAMS\{install_name}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{install_name}" "DisplayName" "{app_name}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{install_name}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{install_name}" "DisplayVersion" "{app_version}"
SectionEnd

Section "Uninstall"
{uninstall_files}
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
    Delete "$SMPROGRAMS\{install_name}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\{install_name}"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{install_name}"
SectionEnd
"""
