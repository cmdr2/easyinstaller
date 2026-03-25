from __future__ import annotations

import pytest

from easyinstaller.builders import build_rpm

from tests.conftest import base_cfg
from tests_integration.conftest import require_commands, require_host_os, run_command


pytestmark = pytest.mark.integration


class TestRpmIntegration:
    def test_builds_rpm_and_exposes_expected_contents(self, source_dir, tmp_path):
        require_host_os("linux")
        require_commands("rpmbuild", "rpm")

        cfg = base_cfg(source_dir, str(tmp_path / "test-app"), target_type="rpm", app_name="Test App")
        result = build_rpm(cfg)

        info = run_command(["rpm", "-qip", result]).stdout.lower()
        contents = run_command(["rpm", "-qlp", result]).stdout
        assert "test-app" in info
        assert "/opt/test-app" in contents
        assert "/opt/test-app/hello.txt" in contents