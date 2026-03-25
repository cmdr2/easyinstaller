from __future__ import annotations

import os
import plistlib
import subprocess

import pytest

from easyinstaller.builders import build_app

from tests.conftest import base_cfg
from tests_integration.conftest import require_host_os


pytestmark = pytest.mark.integration


class TestBuildAppIntegration:
    def test_creates_app_bundle(self, source_dir, output_path):
        require_host_os("mac")

        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app", arch="arm64", app_exec="myapp")
        result = build_app(cfg)
        assert result.endswith(".app")
        assert os.path.isdir(result)

    def test_info_plist_and_resources(self, source_dir, output_path):
        require_host_os("mac")

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="app",
            arch="arm64",
            app_exec="myapp",
            app_name="TestApp",
            app_version="1.2.3",
        )
        result = build_app(cfg)
        with open(os.path.join(result, "Contents", "Info.plist"), "rb") as handle:
            plist = plistlib.load(handle)
        assert plist["CFBundleName"] == "TestApp"
        assert plist["CFBundleVersion"] == "1.2.3"
        assert os.path.isfile(os.path.join(result, "Contents", "Resources", "hello.txt"))

    def test_launcher_executes_packaged_binary(self, source_dir, output_path):
        require_host_os("mac")

        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app", arch="arm64", app_exec="myapp")
        result = build_app(cfg)
        launcher = os.path.join(result, "Contents", "MacOS", "myapp")

        completed = subprocess.run([launcher], check=True, capture_output=True, text=True)
        assert completed.stdout.strip() == "running"
