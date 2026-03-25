from __future__ import annotations

import pytest

from easyinstaller.cli import main


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
        ret = main(
            [
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
            ]
        )
        assert ret == 1
