from __future__ import annotations

import pytest

from easyinstaller.builders import build_app_in_pkg

from tests.conftest import base_cfg


class TestBuildAppInPkg:
    def test_requires_exec(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app-in-pkg", arch="arm64")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_app_in_pkg(cfg)

    def test_uses_pkgbuild_with_component_install(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        patch_run("easyinstaller.builders.mac_support")

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
            call["args"][:2] == ["pkgbuild", "--component"]
            and call["args"][-1] == result
            and "/Applications" in call["args"]
            for call in calls
        )

    def test_notarized_app_in_pkg_signs_app_and_installer(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        patch_run("easyinstaller.builders.mac_support")

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
            call["args"][:2] == ["pkgbuild", "--component"]
            and "--sign" in call["args"]
            and "Developer ID Installer: Example, Inc. (TEAMID1234)" in call["args"]
            for call in calls
        )
        assert any(
            call["args"][:3] == ["xcrun", "notarytool", "submit"] and call["args"][3] == result for call in calls
        )
        assert any(call["args"][:3] == ["xcrun", "stapler", "staple"] and call["args"][-1] == result for call in calls)
