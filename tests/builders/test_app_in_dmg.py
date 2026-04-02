from __future__ import annotations

from pathlib import Path

import pytest

from easyinstaller.builders import build_app_in_dmg
from easyinstaller.builders.mac_support import _write_app_dmg_background

from tests.conftest import base_cfg


class TestBuildAppInDmg:
    def test_writes_static_background_image(self, tmp_path):
        background_path = Path(_write_app_dmg_background(str(tmp_path)))
        template_path = Path(
            __import__("easyinstaller.builders.mac_support", fromlist=["__file__"]).__file__
        ).with_name("app_dmg_background.png")

        assert background_path.is_file()
        assert background_path.read_bytes() == template_path.read_bytes()

    def test_requires_exec(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app-in-dmg", arch="arm64")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_app_in_dmg(cfg)

    def test_adds_applications_alias_to_dmg_layout(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        patch_run("easyinstaller.builders.mac_support")

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="app-in-dmg",
            arch="arm64",
            app_name="Test App",
            app_exec="myapp",
        )
        build_app_in_dmg(cfg)

        assert any(call["args"][0] == "osascript" for call in calls)
        alias_call = next(
            call
            for call in calls
            if call["args"][0] == "osascript"
            and 'to POSIX file "/Applications"' in " ".join(str(arg) for arg in call["args"])
        )
        layout_call = next(
            call
            for call in calls
            if call["args"][0] == "osascript"
            and "background picture of opts" in " ".join(str(arg) for arg in call["args"])
        )
        assert 'name:"Applications"' in " ".join(str(arg) for arg in alias_call["args"])
        layout_script = " ".join(str(arg) for arg in layout_call["args"])
        assert 'set position of item "Test App.app" of diskFolder to {170, 180}' in layout_script
        assert 'set position of item "Applications" of diskFolder to {470, 180}' in layout_script

    def test_builds_dmg_and_staples_when_notarized(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        patch_run("easyinstaller.builders.mac_support")

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="app-in-dmg",
            arch="arm64",
            app_exec="myapp",
            mac_notarize=True,
            mac_notary_team_name="Example, Inc.",
            mac_notary_team_id="TEAMID1234",
            mac_notary_keychain_profile="notary-profile",
        )
        result = build_app_in_dmg(cfg)

        assert result.endswith(".dmg")
        assert any(call["args"][:2] == ["hdiutil", "create"] and "UDRW" in call["args"] for call in calls)
        assert any(call["args"][:2] == ["hdiutil", "convert"] and "UDZO" in call["args"] for call in calls)
        assert any(
            call["args"][:3] == ["xcrun", "notarytool", "submit"] and call["args"][3] == result for call in calls
        )
        assert any(call["args"][:3] == ["xcrun", "stapler", "staple"] and call["args"][-1] == result for call in calls)
