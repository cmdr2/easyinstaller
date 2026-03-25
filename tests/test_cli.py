from __future__ import annotations

import os

import pytest

from easy_installer.cli import main


class TestCLI:
    def test_help(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_missing_required(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--source", "/tmp", "--os", "linux", "--arch", "x86_64", "--type", "zip"])
        assert exc_info.value.code == 2

    def test_invalid_os(self, source_dir):
        ret = main([
            "--source",
            source_dir,
            "--os",
            "bsd",
            "--arch",
            "x86_64",
            "--type",
            "zip",
            "--output",
            "/tmp/test-out",
        ])
        assert ret == 1

    def test_end_to_end_zip(self, source_dir, output_path):
        ret = main(["--source", source_dir, "--os", "linux", "--arch", "x86_64", "--type", "zip", "--output", output_path])
        assert ret == 0
        assert os.path.isfile(output_path + ".zip")

    def test_end_to_end_tar_gz(self, source_dir, output_path):
        ret = main(["--source", source_dir, "--os", "linux", "--arch", "x86_64", "--type", "tar.gz", "--output", output_path])
        assert ret == 0
        assert os.path.isfile(output_path + ".tar.gz")

    def test_end_to_end_app(self, source_dir, output_path):
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
        assert os.path.isdir(output_path + ".app")

    def test_output_folder_path_uses_last_segment_as_filename(self, source_dir, tmp_path):
        output_dir = str(tmp_path / "packages" / "release") + os.sep
        ret = main(["--source", source_dir, "--os", "linux", "--arch", "x86_64", "--type", "zip", "--output", output_dir])
        assert ret == 0
        assert os.path.isfile(str(tmp_path / "packages" / "release" / "release.zip"))