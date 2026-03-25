from __future__ import annotations

import os
from pathlib import Path

from easyinstaller.builders import build_rpm

from tests.conftest import base_cfg


class TestBuildRpm:
    def test_generates_spec_and_copies_built_rpm(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def fake_rpmbuild(args, _kwargs):
            rpm_root = args[2].removeprefix("_topdir ")
            spec_path = Path(args[-1])
            captured["spec"] = spec_path.read_text()
            built_dir = Path(rpm_root) / "RPMS" / "x86_64"
            built_dir.mkdir(parents=True, exist_ok=True)
            (built_dir / "my-spaced-app.rpm").write_text("fake rpm")

        patch_run("easyinstaller.builders.rpm", side_effect=fake_rpmbuild)

        cfg = base_cfg(source_dir, output_path, target_type="rpm", app_name="My Spaced App", app_version="1.0.0")
        result = build_rpm(cfg)

        assert result.endswith(".rpm")
        assert os.path.isfile(result)
        assert "Name:           my-spaced-app" in captured["spec"]
        assert any(call["args"][0] == "rpmbuild" and "x86_64" in call["args"] for call in calls)
