from __future__ import annotations

import os

import pytest

from easyinstaller.builders import build

from .conftest import base_cfg, require_commands


pytestmark = pytest.mark.integration


class TestDispatcher:
    def test_creates_parent_dir(self, source_dir, tmp_path):
        nested_output = str(tmp_path / "new" / "nested" / "dir" / "output")
        cfg = base_cfg(source_dir, nested_output, target_type="zip")
        result = build(cfg)
        assert os.path.isfile(result)
        assert result.endswith(".zip")


class TestIntegrationRequirements:
    def test_require_commands_fails_when_tool_missing(self, monkeypatch):
        monkeypatch.setattr("tests_integration.conftest.shutil.which", lambda command: None)

        with pytest.raises(pytest.fail.Exception, match="missing required commands: missing-tool"):
            require_commands("missing-tool")
