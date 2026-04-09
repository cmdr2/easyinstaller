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

    def test_writes_snap_metadata_and_copies_built_output(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def fake_snap(args, kwargs):
            snap_dir = Path(kwargs["cwd"])
            captured["snap"] = (snap_dir / "meta" / "snap.yaml").read_text()
            (snap_dir / "output.snap").write_text("fake snap")

        patch_run("easyinstaller.builders.snap", side_effect=fake_snap)

        cfg = base_cfg(source_dir, output_path, target_type="snap", app_name="My App", app_exec="myapp")
        result = build_snap(cfg)

        assert result.endswith(".snap")
        assert os.path.isfile(result)
        assert "name: my-app" in captured["snap"]
        assert "base: core24" in captured["snap"]
        assert "command: myapp" in captured["snap"]
        assert any(call["args"][:2] == ["snap", "pack"] for call in calls)
