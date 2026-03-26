from __future__ import annotations

import pytest
from pathlib import Path

from easyinstaller.builders import build_app_in_pkg

from tests.conftest import base_cfg


class TestBuildAppInPkg:
    @staticmethod
    def _write_synthesized_distribution(args) -> None:
        if args[:2] != ["productbuild", "--synthesize"]:
            return
        Path(args[-1]).write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<installer-gui-script minSpecVersion="1">\n'
            '    <pkg-ref id="com.test.pkg"/>\n'
            '    <options customize="never" require-scripts="false"/>\n'
            "    <choices-outline>\n"
            '        <line choice="default"/>\n'
            "    </choices-outline>\n"
            '    <choice id="default"/>\n'
            '    <pkg-ref id="com.test.pkg" version="1.0.0">component.pkg</pkg-ref>\n'
            "</installer-gui-script>\n"
        )

    def test_requires_exec(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app-in-pkg", arch="arm64")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_app_in_pkg(cfg)

    def test_wraps_pkgbuild_component_with_productbuild(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy

        def inspect_calls(args, _kwargs):
            self._write_synthesized_distribution(args)

        patch_run("easyinstaller.builders.mac_support", side_effect=inspect_calls)

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="app-in-pkg",
            arch="arm64",
            app_name="TestApp",
            app_version="1.2.3",
            app_exec="myapp",
        )
        result = build_app_in_pkg(cfg)

        assert result.endswith(".pkg")
        assert any(
            call["args"][:2] == ["pkgbuild", "--component"]
            and "--identifier" in call["args"]
            and call["args"][call["args"].index("--identifier") + 1] == "com.testapp.app.pkg"
            for call in calls
        )
        assert any(
            call["args"][:2] == ["pkgbuild", "--component"] and "/Applications" in call["args"] for call in calls
        )
        assert any(call["args"][:2] == ["productbuild", "--synthesize"] for call in calls)
        assert any(
            call["args"][:2] == ["productbuild", "--distribution"] and call["args"][-1] == result for call in calls
        )

    def test_notarized_app_in_pkg_signs_app_and_installer(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy

        def inspect_calls(args, _kwargs):
            self._write_synthesized_distribution(args)

        patch_run("easyinstaller.builders.mac_support", side_effect=inspect_calls)

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="app-in-pkg",
            arch="arm64",
            app_name="TestApp",
            app_version="1.2.3",
            app_exec="myapp",
            mac_notarize=True,
            mac_notary_team_name="Example, Inc.",
            mac_notary_team_id="TEAMID1234",
            mac_notary_keychain_profile="notary-profile",
        )
        result = build_app_in_pkg(cfg)

        assert any(
            call["args"][:2] == ["codesign", "--force"]
            and "Developer ID Application: Example, Inc. (TEAMID1234)" in call["args"]
            for call in calls
        )
        assert any(
            call["args"][:2] == ["productbuild", "--distribution"]
            and "--sign" in call["args"]
            and "Developer ID Installer: Example, Inc. (TEAMID1234)" in call["args"]
            for call in calls
        )
        assert any(
            call["args"][:3] == ["xcrun", "notarytool", "submit"] and call["args"][3] == result for call in calls
        )
        assert any(call["args"][:3] == ["xcrun", "stapler", "staple"] and call["args"][-1] == result for call in calls)
