from __future__ import annotations

import os
import plistlib
import tarfile
import zipfile

import pytest

from easyinstaller.cli import main

from .conftest import require_host_os


pytestmark = pytest.mark.integration


class TestCLIIntegration:
    def test_end_to_end_zip_extracts_expected_files(self, source_dir, output_path):
        ret = main(
            ["--source", source_dir, "--os", "linux", "--arch", "x86_64", "--type", "zip", "--output", output_path]
        )
        assert ret == 0

        result = output_path + ".zip"
        assert os.path.isfile(result)
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
        assert any(name.endswith("hello.txt") for name in names)
        assert any(name.endswith("subdir/nested.txt") for name in names)

    def test_end_to_end_tar_gz_extracts_expected_files(self, source_dir, output_path):
        ret = main(
            ["--source", source_dir, "--os", "linux", "--arch", "x86_64", "--type", "tar.gz", "--output", output_path]
        )
        assert ret == 0

        result = output_path + ".tar.gz"
        assert os.path.isfile(result)
        with tarfile.open(result) as tf:
            names = tf.getnames()
        assert any(name.endswith("hello.txt") for name in names)
        assert any(name.endswith("subdir/nested.txt") for name in names)

    def test_output_folder_path_uses_last_segment_as_filename(self, source_dir, tmp_path):
        output_dir = str(tmp_path / "packages" / "release") + os.sep
        ret = main(
            ["--source", source_dir, "--os", "linux", "--arch", "x86_64", "--type", "zip", "--output", output_dir]
        )
        assert ret == 0
        assert os.path.isfile(str(tmp_path / "packages" / "release" / "release.zip"))

    def test_end_to_end_app_creates_valid_bundle_on_mac(self, source_dir, output_path):
        require_host_os("mac")

        ret = main(
            [
                "--source",
                source_dir,
                "--os",
                "mac",
                "--arch",
                "arm64",
                "--type",
                "app",
                "--output",
                output_path,
                "--app-name",
                "TestApp",
                "--app-exec",
                "myapp",
            ]
        )
        assert ret == 0

        app_root = output_path + ".app"
        assert os.path.isdir(app_root)
        with open(os.path.join(app_root, "Contents", "Info.plist"), "rb") as handle:
            plist = plistlib.load(handle)
        assert plist["CFBundleName"] == "TestApp"
        assert plist["CFBundleExecutable"] == "myapp"
