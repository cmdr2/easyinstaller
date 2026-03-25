from __future__ import annotations

import pytest

from easy_installer.builders import build_app_in_dmg

from tests.conftest import base_cfg


class TestBuildAppInDmg:
    def test_requires_exec(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app-in-dmg", arch="arm64")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_app_in_dmg(cfg)

    def test_builds_dmg_and_staples_when_notarized(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        patch_run("easy_installer.builders.mac_support")

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="app-in-dmg",
            arch="arm64",
            app_exec="myapp",
            mac_notarize=True,
            mac_sign_identity="Developer ID Application: Example",
            mac_notary_keychain_profile="notary-profile",
        )
        result = build_app_in_dmg(cfg)

        assert result.endswith(".dmg")
        assert any(call["args"][:2] == ["hdiutil", "create"] for call in calls)
        assert any(
            call["args"][:3] == ["xcrun", "notarytool", "submit"] and call["args"][3] == result for call in calls
        )
        assert any(call["args"][:3] == ["xcrun", "stapler", "staple"] and call["args"][-1] == result for call in calls)
