from __future__ import annotations

import os
import tarfile

from easy_installer.builders import build_tar_gz

from tests.conftest import base_cfg


class TestBuildTarGz:
    def test_creates_tar_gz_for_each_supported_os(self, source_dir, tmp_path):
        cases = [("windows", "x86_64"), ("linux", "x86_64"), ("mac", "arm64")]
        for target_os, arch in cases:
            output = str(tmp_path / f"{target_os}-targz")
            cfg = base_cfg(source_dir, output, target_os=target_os, arch=arch, target_type="tar.gz")
            result = build_tar_gz(cfg)
            assert result.endswith(".tar.gz")
            assert os.path.isfile(result)

    def test_tar_gz_contents(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_type="tar.gz")
        result = build_tar_gz(cfg)
        with tarfile.open(result) as tf:
            names = tf.getnames()
            assert any("hello.txt" in name for name in names)
            assert any("nested.txt" in name for name in names)