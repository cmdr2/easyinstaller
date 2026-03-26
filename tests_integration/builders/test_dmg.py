from __future__ import annotations

from pathlib import Path

import pytest

from easyinstaller.builders import build_dmg

from tests.conftest import base_cfg
from tests_integration.conftest import mount_dmg, require_commands, require_host_os, unmount_dmg


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
            assert (mount_path / "hello.txt").is_file()
            assert (mount_path / "subdir" / "nested.txt").is_file()
        finally:
            unmount_dmg(mount_path)
