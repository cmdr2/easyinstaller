from __future__ import annotations

import os
from pathlib import Path

import pytest

from easyinstaller.builders import build_snap

from tests.conftest import base_cfg


class TestBuildSnap:
    def test_requires_exec(self, source_dir, output_path, command_spy):
        _calls, patch_run, _patch_subprocess = command_spy
        patch_run("easyinstaller.builders.snap")
        cfg = base_cfg(source_dir, output_path, target_type="snap")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_snap(cfg)

    def test_writes_snapcraft_and_copies_built_output(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def fake_snapcraft(args, kwargs):
            snap_dir = Path(kwargs["cwd"])
            captured["snapcraft"] = (snap_dir / "snap" / "snapcraft.yaml").read_text()
            (snap_dir / "my-app_1.0.0_amd64.snap").write_text("fake snap")

        patch_run("easyinstaller.builders.snap", side_effect=fake_snapcraft)

        cfg = base_cfg(source_dir, output_path, target_type="snap", app_name="My App", app_exec="myapp")
        result = build_snap(cfg)

        assert result.endswith(".snap")
        assert os.path.isfile(result)
        assert "name: my-app" in captured["snapcraft"]
        assert "command: myapp" in captured["snapcraft"]
        assert any(call["args"][:2] == ["snapcraft", "pack"] for call in calls)
