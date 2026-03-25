"""Configuration, validation and normalisation helpers."""

from __future__ import annotations

import dataclasses
import os
from typing import Optional

# ── Supported values ─────────────────────────────────────────────────────────

SUPPORTED_OS = ("windows", "linux", "mac")

SUPPORTED_ARCH = ("x86_64", "arm64", "i386", "armhf")

TYPES_BY_OS: dict[str, tuple[str, ...]] = {
    "windows": ("zip", "tar.gz", "nsis"),
    "linux": ("zip", "tar.gz", "deb", "rpm", "appimage", "flatpak", "snap"),
    "mac": ("zip", "tar.gz", "dmg", "app"),
}

OS_ALIASES: dict[str, str] = {
    "win": "windows",
    "windows": "windows",
    "linux": "linux",
    "mac": "mac",
    "macos": "mac",
    "osx": "mac",
}

ARCH_ALIASES: dict[str, str] = {
    "x86_64": "x86_64",
    "amd64": "x86_64",
    "x64": "x86_64",
    "arm64": "arm64",
    "aarch64": "arm64",
    "i386": "i386",
    "i686": "i386",
    "x86": "i386",
    "armhf": "armhf",
    "armv7l": "armhf",
}

TYPE_ALIASES: dict[str, str] = {
    "zip": "zip",
    "tar.gz": "tar.gz",
    "targz": "tar.gz",
    "tgz": "tar.gz",
    "nsis": "nsis",
    "deb": "deb",
    "rpm": "rpm",
    "appimage": "appimage",
    "flatpak": "flatpak",
    "snap": "snap",
    "dmg": "dmg",
    "app": "app",
}


# ── Data class ───────────────────────────────────────────────────────────────


@dataclasses.dataclass
class Config:
    """Validated, normalised build configuration."""

    source: str
    target_os: str
    arch: str
    target_type: str
    output: str

    # Optional metadata used by some formats
    app_name: str = ""
    app_version: str = "1.0.0"
    app_description: str = "Application packaged with easyinstaller"
    app_maintainer: str = "maintainer@example.com"
    app_category: str = "Utility"
    app_exec: Optional[str] = None
    app_icon: Optional[str] = None


# ── Validation ───────────────────────────────────────────────────────────────


class ConfigError(Exception):
    """Raised when configuration is invalid."""


def validate_and_normalise(cfg: Config) -> Config:
    """Return a new *Config* with normalised fields, or raise *ConfigError*."""

    # Source directory
    source = os.path.abspath(cfg.source)
    if not os.path.isdir(source):
        raise ConfigError(f"Source directory does not exist: {cfg.source}")

    # OS
    target_os = OS_ALIASES.get(cfg.target_os.lower())
    if target_os is None:
        raise ConfigError(f"Unsupported OS: {cfg.target_os}. " f"Use one of: {', '.join(SUPPORTED_OS)}")

    # Arch
    arch = ARCH_ALIASES.get(cfg.arch.lower())
    if arch is None:
        raise ConfigError(f"Unsupported arch: {cfg.arch}. " f"Use one of: {', '.join(SUPPORTED_ARCH)}")

    # Type
    target_type = TYPE_ALIASES.get(cfg.target_type.lower())
    if target_type is None:
        raise ConfigError(f"Unsupported type: {cfg.target_type}. " f"Use one of: {', '.join(TYPE_ALIASES)}")

    # OS + type combination
    allowed = TYPES_BY_OS[target_os]
    if target_type not in allowed:
        raise ConfigError(
            f"Type '{target_type}' is not supported for {target_os}. " f"Use one of: {', '.join(allowed)}"
        )

    # Output — resolve to absolute
    output = cfg.output if os.path.isabs(cfg.output) else os.path.join(os.getcwd(), cfg.output)

    # App name default
    app_name = cfg.app_name or os.path.basename(output)

    return dataclasses.replace(
        cfg,
        source=source,
        target_os=target_os,
        arch=arch,
        target_type=target_type,
        output=output,
        app_name=app_name,
    )
