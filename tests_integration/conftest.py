from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import base_cfg, output_path, source_dir

HOST_OS = {
    "win32": "windows",
    "linux": "linux",
    "darwin": "mac",
}.get(sys.platform, sys.platform)


def require_host_os(expected: str) -> None:
    if HOST_OS != expected:
        pytest.skip(f"requires {expected} host")


def require_commands(*commands: str) -> None:
    missing = [command for command in commands if shutil.which(command) is None]
    if missing:
        pytest.skip(f"missing required commands: {', '.join(missing)}")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def mount_dmg(image_path: str, mount_path: Path) -> None:
    run_command(
        [
            "hdiutil",
            "attach",
            "-nobrowse",
            "-readonly",
            "-mountpoint",
            str(mount_path),
            image_path,
        ]
    )


def unmount_dmg(mount_path: Path) -> None:
    run_command(["hdiutil", "detach", str(mount_path)])


def assert_contains_any(root: Path, candidates: list[Path]) -> None:
    assert any((root / candidate).exists() for candidate in candidates)
