from __future__ import annotations

import os

import pytest

from easyinstaller.builders import build_appimage

from tests.conftest import base_cfg
from tests_integration.conftest import require_commands, require_host_os


pytestmark = pytest.mark.integration


class TestAppImageIntegration:
    def test_builds_appimage_bundle(self, source_dir, tmp_path):
        require_host_os("linux")
        require_commands("appimagetool")

        cfg = base_cfg(
            source_dir,
            str(tmp_path / "test-appimage"),
            target_type="appimage",
            app_name="TestApp",
            app_exec="myapp",
        )
        result = build_appimage(cfg)

        assert result.endswith(".AppImage")
        assert os.path.isfile(result)
        assert os.path.getsize(result) > 0