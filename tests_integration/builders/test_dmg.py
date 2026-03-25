from __future__ import annotations

from pathlib import Path

import pytest

from easyinstaller.builders import build_dmg

from tests.conftest import base_cfg
from tests_integration.conftest import assert_contains_any, mount_dmg, require_commands, require_host_os, unmount_dmg


pytestmark = pytest.mark.integration


class TestDmgIntegration:
    def test_builds_dmg_and_mounts_expected_contents(self, source_dir, tmp_path):
        require_host_os("mac")
        require_commands("hdiutil")

        cfg = base_cfg(source_dir, str(tmp_path / "test-dmg"), target_os="mac", target_type="dmg", arch="arm64")
        result = build_dmg(cfg)
        mount_path = tmp_path / "mounted-dmg"
        mount_path.mkdir()

        mount_dmg(result, mount_path)
        try:
            source_name = Path(source_dir).name
            assert_contains_any(mount_path, [Path("hello.txt"), Path(source_name) / "hello.txt"])
            assert_contains_any(mount_path, [Path("subdir") / "nested.txt", Path(source_name) / "subdir" / "nested.txt"])
        finally:
            unmount_dmg(mount_path)