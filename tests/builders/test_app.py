from __future__ import annotations

import os
import plistlib
from pathlib import Path

import pytest

from easyinstaller.builders import build_app

from tests.conftest import base_cfg


class TestBuildApp:
    def test_writes_valid_plist_for_special_characters(self, source_dir, output_path):
        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="app",
            arch="arm64",
            app_exec="myapp",
            app_name='Test & <App> "Name"',
            app_version="1.2.3 & <beta>",
        )

        result = build_app(cfg)
        with open(os.path.join(result, "Contents", "Info.plist"), "rb") as handle:
            plist = plistlib.load(handle)

        assert plist["CFBundleName"] == 'Test & <App> "Name"'
        assert plist["CFBundleVersion"] == "1.2.3 & <beta>"

    def test_nested_app_exec_uses_basename_for_bundle_launcher(self, tmp_path):
        source = tmp_path / "source"
        nested = source / "bin"
        nested.mkdir(parents=True)
        executable = nested / "myapp"
        executable.write_text("#!/bin/bash\necho nested\n")
        executable.chmod(0o755)

        cfg = base_cfg(
            str(source),
            str(tmp_path / "output"),
            target_os="mac",
            target_type="app",
            arch="arm64",
            app_exec="bin/myapp",
        )

        result = build_app(cfg)
        with open(os.path.join(result, "Contents", "Info.plist"), "rb") as handle:
            plist = plistlib.load(handle)
        launcher = os.path.join(result, "Contents", "MacOS", "myapp")
        launcher_text = Path(launcher).read_text()

        assert plist["CFBundleExecutable"] == "myapp"
        assert 'exec "${DIR}/bin/myapp" "$@"' in launcher_text

    def test_requires_exec(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app", arch="arm64")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_app(cfg)

    def test_staples_when_notarized(self, source_dir, output_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        patch_run("easyinstaller.builders.mac_support")

        cfg = base_cfg(
            source_dir,
            output_path,
            target_os="mac",
            target_type="app",
            arch="arm64",
            app_exec="myapp",
            mac_notarize=True,
            mac_notary_team_name="Example, Inc.",
            mac_notary_team_id="TEAMID1234",
            mac_notary_keychain_profile="notary-profile",
        )
        result = build_app(cfg)

        staple_calls = [call for call in calls if call["args"][:3] == ["xcrun", "stapler", "staple"]]

        assert any(
            call["args"][:3] == ["xcrun", "notarytool", "submit"] and call["args"][3] == result for call in calls
        )
        assert any(call["args"][:3] == ["xcrun", "stapler", "staple"] and call["args"][-1] == result for call in calls)
        assert staple_calls[0]["kwargs"] == {"stdout": -1, "stderr": -1, "text": True}
