from __future__ import annotations

import plistlib
from pathlib import Path

import pytest

from easyinstaller.builders import build_app_in_dmg

from tests.conftest import base_cfg
from tests_integration.conftest import mount_dmg, require_commands, require_host_os, unmount_dmg


pytestmark = pytest.mark.integration


class TestAppInDmgIntegration:
    def test_builds_app_in_dmg_and_mounts_app_bundle(self, source_dir, tmp_path):
        require_host_os("mac")
        require_commands("hdiutil")

        cfg = base_cfg(
            source_dir,
            str(tmp_path / "test-app-in-dmg"),
            target_os="mac",
            target_type="app-in-dmg",
            arch="arm64",
            app_name="TestApp",
            app_exec="myapp",
        )
        result = build_app_in_dmg(cfg)
        mount_path = tmp_path / "mounted-app-dmg"
        mount_path.mkdir()

        mount_dmg(result, mount_path)
        try:
            app_root = mount_path / "TestApp.app"
            assert app_root.is_dir()
            with open(app_root / "Contents" / "Info.plist", "rb") as handle:
                plist = plistlib.load(handle)
            assert plist["CFBundleExecutable"] == "myapp"
            assert (app_root / "Contents" / "Resources" / "hello.txt").is_file()
        finally:
            unmount_dmg(mount_path)