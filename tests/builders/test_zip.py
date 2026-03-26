from __future__ import annotations

from easyinstaller.builders import build_zip

from tests.conftest import base_cfg


class TestBuildZip:
    def test_zip_mac_notarization_submits_without_stapling(self, tmp_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        patch_run("easyinstaller.builders.mac_support")

        source = tmp_path / "src"
        source.mkdir()
        executable = source / "runme"
        executable.write_text("#!/bin/bash\nexit 0\n")
        executable.chmod(0o755)

        cfg = base_cfg(
            str(source),
            str(tmp_path / "out"),
            target_os="mac",
            arch="arm64",
            target_type="zip",
            mac_notarize=True,
            mac_notary_team_name="Example, Inc.",
            mac_notary_team_id="TEAMID1234",
            mac_notary_keychain_profile="notary-profile",
        )
        build_zip(cfg)

        submit_calls = [call for call in calls if call["args"][:3] == ["xcrun", "notarytool", "submit"]]

        assert submit_calls
        assert submit_calls[0]["kwargs"] == {"stdout": -1, "stderr": -1, "text": True}
        assert not any(call["args"][:3] == ["xcrun", "stapler", "staple"] for call in calls)
