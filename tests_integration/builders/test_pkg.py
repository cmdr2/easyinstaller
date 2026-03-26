from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from easyinstaller.builders import build_pkg
from easyinstaller.builders.common import _sanitise_name

from tests.conftest import base_cfg
from tests_integration.conftest import install_pkg, require_commands, require_host_os


pytestmark = pytest.mark.integration


class TestPkgIntegration:
    def test_builds_pkg_and_installs_release_tree(self, source_dir, tmp_path):
        require_host_os("mac")
        require_commands("productbuild", "installer")

        app_name = "TestPkgInstall"
        installed_root = Path.home() / "opt" / _sanitise_name(app_name)
        installed_launcher = Path.home() / "usr" / "local" / "bin" / "myapp"
        shutil.rmtree(installed_root, ignore_errors=True)
        installed_launcher.unlink(missing_ok=True)

        cfg = base_cfg(
            source_dir,
            str(tmp_path / "test-pkg"),
            target_os="mac",
            target_type="pkg",
            arch="arm64",
            app_name=app_name,
            app_exec="myapp",
        )

        try:
            result = build_pkg(cfg)
            install_pkg(result)

            assert installed_root.is_dir()
            assert (installed_root / "hello.txt").is_file()
            assert (installed_root / "subdir" / "nested.txt").is_file()
            assert (installed_root / "myapp").is_file()
            assert installed_launcher.is_file()
            assert installed_launcher.read_text().startswith("#!/bin/bash\n")
        finally:
            shutil.rmtree(installed_root, ignore_errors=True)
            installed_launcher.unlink(missing_ok=True)
