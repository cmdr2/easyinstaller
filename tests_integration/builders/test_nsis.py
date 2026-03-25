from __future__ import annotations

import os

import pytest

from easyinstaller.builders import build_nsis

from tests.conftest import base_cfg
from tests_integration.conftest import require_commands, require_host_os


pytestmark = pytest.mark.integration


class TestNsisIntegration:
    def test_builds_nsis_installer(self, source_dir, tmp_path):
        require_host_os("windows")
        require_commands("makensis")

        cfg = base_cfg(source_dir, str(tmp_path / "setup"), target_os="windows", target_type="nsis", app_name="TestApp")
        result = build_nsis(cfg)

        assert result.endswith(".exe")
        assert os.path.isfile(result)
        assert os.path.getsize(result) > 0