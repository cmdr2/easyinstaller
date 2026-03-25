from __future__ import annotations

import os

from easy_installer.builders import build

from .conftest import base_cfg


class TestDispatcher:
    def test_creates_parent_dir(self, source_dir, tmp_path):
        nested_output = str(tmp_path / "new" / "nested" / "dir" / "output")
        cfg = base_cfg(source_dir, nested_output, target_type="zip")
        result = build(cfg)
        assert os.path.isfile(result)
        assert result.endswith(".zip")
