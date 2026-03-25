from __future__ import annotations

import pytest

from easyinstaller.builders import build_deb

from tests.conftest import base_cfg
from tests_integration.conftest import require_commands, require_host_os, run_command


pytestmark = pytest.mark.integration


class TestDebIntegration:
    def test_builds_deb_and_exposes_expected_contents(self, source_dir, tmp_path):
        require_host_os("linux")
        require_commands("dpkg-deb")

        cfg = base_cfg(
            source_dir,
            str(tmp_path / "test-app"),
            target_type="deb",
            app_name="Test App",
            app_exec="myapp",
        )
        result = build_deb(cfg)

        info = run_command(["dpkg-deb", "--info", result]).stdout
        contents = run_command(["dpkg-deb", "--contents", result]).stdout
        assert "Package: test-app" in info
        assert "opt/test-app/hello.txt" in contents
        assert "usr/bin/myapp" in contents