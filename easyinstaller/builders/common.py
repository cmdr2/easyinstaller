"""Shared builder helpers."""

from __future__ import annotations

import logging
import shutil
import subprocess

log = logging.getLogger("easyinstaller")


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


def _flatpak_arch(arch: str) -> str:
    return {"x86_64": "x86_64", "arm64": "aarch64", "i386": "i386", "armhf": "arm"}[arch]


def _sanitise_name(name: str) -> str:
    """Lower-case, replace non-alphanumeric with hyphens, collapse multiples."""
    import re

    value = name.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")
