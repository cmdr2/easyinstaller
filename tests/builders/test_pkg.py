from __future__ import annotations

from pathlib import Path

from easyinstaller.builders import build_pkg

from tests.conftest import base_cfg


class TestBuildPkg:
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

    def test_wraps_pkgbuild_root_with_productbuild(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy

        staged_root_has_payload: list[bool] = []

        def inspect_pkg_root(args, _kwargs):
            if args[:2] == ["pkgbuild", "--root"]:
                staged_root = Path(args[2])
                staged_root_has_payload.append((staged_root / "opt" / "test-app" / "hello.txt").is_file())
            self._write_synthesized_distribution(args)

        patch_run("easyinstaller.builders.mac_support", side_effect=inspect_pkg_root)

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="pkg",
            arch="arm64",
            app_name="Test App",
            app_version="1.2.3",
        )
        result = build_pkg(cfg)

        assert result.endswith(".pkg")
        assert staged_root_has_payload == [True]
        assert any(
            call["args"][:2] == ["pkgbuild", "--root"]
            and "--identifier" in call["args"]
            and call["args"][call["args"].index("--identifier") + 1] == "com.testapp.pkg"
            for call in calls
        )
        assert any(
            call["args"][:2] == ["productbuild", "--synthesize"] and "--package" in call["args"] for call in calls
        )
        assert any(
            call["args"][:2] == ["productbuild", "--distribution"] and call["args"][-1] == result for call in calls
        )

    def test_pkg_adds_launcher_when_app_exec_is_set(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy

        launcher_text: list[str] = []

        def inspect_pkg_root(args, _kwargs):
            if args[:2] == ["pkgbuild", "--root"]:
                launcher_path = Path(args[2]) / "usr" / "local" / "bin" / "myapp"
                launcher_text.append(launcher_path.read_text())
            self._write_synthesized_distribution(args)

        patch_run("easyinstaller.builders.mac_support", side_effect=inspect_pkg_root)

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="pkg",
            arch="arm64",
            app_name="Test App",
            app_version="1.2.3",
            app_exec="myapp",
        )
        build_pkg(cfg)

        assert launcher_text
        assert "../../../opt/test-app" in launcher_text[0]
        assert 'exec "${DIR}/myapp" "$@"' in launcher_text[0]

    def test_notarized_pkg_signs_payload_and_installer(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy

        def inspect_pkg_root(args, _kwargs):
            self._write_synthesized_distribution(args)

        patch_run("easyinstaller.builders.mac_support", side_effect=inspect_pkg_root)

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="pkg",
            arch="arm64",
            app_name="Test App",
            app_version="1.2.3",
            app_exec="myapp",
            mac_notarize=True,
            mac_notary_team_name="Example, Inc.",
            mac_notary_team_id="TEAMID1234",
            mac_notary_keychain_profile="notary-profile",
        )
        result = build_pkg(cfg)

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
