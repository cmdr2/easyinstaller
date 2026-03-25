from __future__ import annotations

import os
import zipfile

import pytest

from easyinstaller.builders import build_zip

from tests.conftest import base_cfg


pytestmark = pytest.mark.integration


class TestBuildZipIntegration:
    def test_creates_zip_for_each_supported_os(self, source_dir, tmp_path):
        cases = [("windows", "x86_64"), ("linux", "x86_64"), ("mac", "arm64")]
        for target_os, arch in cases:
            output = str(tmp_path / f"{target_os}-zip")
            cfg = base_cfg(source_dir, output, target_os=target_os, arch=arch, target_type="zip")
            result = build_zip(cfg)
            assert result.endswith(".zip")
            assert os.path.isfile(result)

    def test_zip_contents(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_type="zip")
        result = build_zip(cfg)
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
        assert any(name.endswith("hello.txt") for name in names)
        assert any(name.endswith("subdir/nested.txt") for name in names)

    def test_zip_preserves_empty_directory(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "file.txt").write_text("data")
        (src / "emptydir").mkdir()

        cfg = base_cfg(str(src), str(tmp_path / "out"), target_type="zip")
        result = build_zip(cfg)
        with zipfile.ZipFile(result) as zf:
            assert any(name.endswith("emptydir/") for name in zf.namelist())
