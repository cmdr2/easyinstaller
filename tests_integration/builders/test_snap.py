from __future__ import annotations

import os

import pytest

from easyinstaller.builders import build_snap

from tests.conftest import base_cfg
from tests_integration.conftest import require_commands, require_host_os


pytestmark = pytest.mark.integration


class TestSnapIntegration:
    def test_builds_snap_bundle(self, source_dir, tmp_path):
        require_host_os("linux")
        require_commands("snap")

        cfg = base_cfg(
            source_dir,
            str(tmp_path / "test-snap"),
            target_type="snap",
            app_name="Test App",
            app_exec="myapp",
        )
        result = build_snap(cfg)

        assert result.endswith(".snap")
        assert os.path.isfile(result)
        assert os.path.getsize(result) > 0
