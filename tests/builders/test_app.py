from __future__ import annotations

import os

import pytest

from easy_installer.builders import build_app

from tests.conftest import base_cfg


class TestBuildApp:
    def test_creates_app_bundle(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app", arch="arm64", app_exec="myapp")
        result = build_app(cfg)
        assert result.endswith(".app")
        assert os.path.isdir(result)

    def test_info_plist_and_resources(self, source_dir, output_path):
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
        plist_path = os.path.join(result, "Contents", "Info.plist")
        with open(plist_path) as handle:
            plist = handle.read()
        assert "TestApp" in plist
        assert "1.2.3" in plist
        assert os.path.isfile(os.path.join(result, "Contents", "Resources", "hello.txt"))

    def test_requires_exec(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app", arch="arm64")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_app(cfg)

    def test_staples_when_notarized(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        patch_run("easy_installer.builders.mac_support")

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="app",
            arch="arm64",
            app_exec="myapp",
            mac_notarize=True,
            mac_sign_identity="Developer ID Application: Example",
            mac_notary_keychain_profile="notary-profile",
        )
        result = build_app(cfg)

        assert any(
            call["args"][:3] == ["xcrun", "notarytool", "submit"] and call["args"][3] == result for call in calls
        )
        assert any(call["args"][:3] == ["xcrun", "stapler", "staple"] and call["args"][-1] == result for call in calls)
