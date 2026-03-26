from __future__ import annotations

import plistlib
import shutil
from pathlib import Path

import pytest

from easyinstaller.builders import build_app_in_pkg

from tests.conftest import base_cfg
from tests_integration.conftest import install_pkg, require_commands, require_host_os


pytestmark = pytest.mark.integration


class TestAppInPkgIntegration:
    def test_builds_app_in_pkg_and_installs_app_bundle(self, source_dir, tmp_path):
        require_host_os("mac")
        require_commands("pkgbuild", "productbuild", "installer")

        app_name = "TestAppInPkg"
        installed_app = Path.home() / "Applications" / f"{app_name}.app"
        shutil.rmtree(installed_app, ignore_errors=True)

        cfg = base_cfg(
            source_dir,
            str(tmp_path / "test-app-in-pkg"),
            target_os="mac",
            target_type="app-in-pkg",
            arch="arm64",
            app_name=app_name,
            app_exec="myapp",
        )

        try:
            result = build_app_in_pkg(cfg)
            install_pkg(result)

            assert installed_app.is_dir()
            with open(installed_app / "Contents" / "Info.plist", "rb") as handle:
                plist = plistlib.load(handle)
            assert plist["CFBundleExecutable"] == "myapp"
            assert (installed_app / "Contents" / "Resources" / "hello.txt").is_file()
        finally:
            shutil.rmtree(installed_app, ignore_errors=True)
