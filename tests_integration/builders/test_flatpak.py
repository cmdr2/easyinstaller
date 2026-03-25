from __future__ import annotations

import os

import pytest

from easyinstaller.builders import build_flatpak

from tests.conftest import base_cfg
from tests_integration.conftest import require_commands, require_host_os


pytestmark = pytest.mark.integration


class TestFlatpakIntegration:
    def test_builds_flatpak_bundle(self, source_dir, tmp_path):
        require_host_os("linux")
        require_commands("flatpak", "flatpak-builder")

        cfg = base_cfg(
            source_dir,
            str(tmp_path / "test-flatpak"),
            target_type="flatpak",
            app_name="TestApp",
            app_exec="myapp",
        )
        result = build_flatpak(cfg)

        assert result.endswith(".flatpak")
        assert os.path.isfile(result)
        assert os.path.getsize(result) > 0