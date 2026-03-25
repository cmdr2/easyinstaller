"""Configuration, validation and normalisation helpers."""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Optional

# ── Supported values ─────────────────────────────────────────────────────────

SUPPORTED_OS = ("windows", "linux", "mac")

SUPPORTED_ARCH = ("x86_64", "arm64", "i386", "armhf")

TYPES_BY_OS: dict[str, tuple[str, ...]] = {
    "windows": ("zip", "tar.gz", "nsis"),
    "linux": ("zip", "tar.gz", "deb", "rpm", "appimage", "flatpak", "snap"),
    "mac": ("zip", "tar.gz", "dmg", "app", "app-in-dmg"),
}

OS_ALIASES: dict[str, str] = {
    "win": "windows",
    "windows": "windows",
    "linux": "linux",
    "mac": "mac",
    "macos": "mac",
    "osx": "mac",
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
    "app-in-dmg": "app-in-dmg",
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
    mac_notarize: bool = False
    mac_sign_identity: Optional[str] = None
    mac_notary_keychain_profile: Optional[str] = None
    mac_notary_apple_id: Optional[str] = None
    mac_notary_team_id: Optional[str] = None
    mac_notary_password: Optional[str] = None


# ── Validation ───────────────────────────────────────────────────────────────


class ConfigError(Exception):
    """Raised when configuration is invalid."""


def _validate_app_exec(source: str, app_exec: Optional[str]) -> None:
    if app_exec is None:
        return

    normalised_exec = app_exec.replace("\\", "/")
    exec_path = PurePosixPath(normalised_exec)
    if exec_path.is_absolute() or PureWindowsPath(app_exec).is_absolute():
        raise ConfigError("--app-exec must be a relative path inside the source directory")

    if any(part in {"", ".", ".."} for part in exec_path.parts):
        raise ConfigError("--app-exec must stay inside the source directory")

    source_exec = os.path.join(source, *exec_path.parts)
    if not os.path.isfile(source_exec):
        raise ConfigError(f"--app-exec does not exist in the source directory: {app_exec}")


def _normalise_output_path(output: str) -> str:
    output_path = Path(output).expanduser()
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path

    output_text = output.replace("/", os.sep).replace("\\", os.sep)
    looks_like_dir = output_text.endswith(os.sep)
    if not looks_like_dir and output_path.exists() and output_path.is_dir():
        looks_like_dir = True

    if looks_like_dir:
        parent = output_path if output_path.name else output_path.parent
        filename = parent.name
        if not filename:
            raise ConfigError(f"Output path must include a folder name: {output}")
        output_path = parent / filename

    return str(output_path)


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

    # Arch
    if cfg.arch not in SUPPORTED_ARCH:
        raise ConfigError(f"Unsupported arch: {cfg.arch}. " f"Use one of: {', '.join(SUPPORTED_ARCH)}")

    _validate_app_exec(source, cfg.app_exec)

    if cfg.mac_notarize:
        if target_os != "mac":
            raise ConfigError("--mac-notarize is only supported for mac targets")
        if not cfg.mac_sign_identity:
            raise ConfigError("--mac-notarize requires --mac-sign-identity")
        if target_type not in {"zip", "dmg", "app", "app-in-dmg"}:
            raise ConfigError("--mac-notarize is only supported for mac types: zip, dmg, app, app-in-dmg")
        has_keychain_profile = bool(cfg.mac_notary_keychain_profile)
        has_direct_credentials = all([cfg.mac_notary_apple_id, cfg.mac_notary_team_id, cfg.mac_notary_password])
        if not has_keychain_profile and not has_direct_credentials:
            raise ConfigError(
                "--mac-notarize requires either --mac-notary-keychain-profile or all of "
                "--mac-notary-apple-id, --mac-notary-team-id, and --mac-notary-password"
            )

    # Output - resolve to absolute
    output = _normalise_output_path(cfg.output)

    # App name default
    app_name = cfg.app_name or os.path.basename(output)

    app_exec = cfg.app_exec.replace("\\", "/") if cfg.app_exec else None

    return dataclasses.replace(
        cfg,
        source=source,
        target_os=target_os,
        arch=cfg.arch,
        target_type=target_type,
        output=output,
        app_name=app_name,
        app_exec=app_exec,
    )
