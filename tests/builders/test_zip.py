from __future__ import annotations

import os
import zipfile

from easy_installer.builders import build_zip

from tests.conftest import base_cfg


class TestBuildZip:
    def test_creates_zip_for_each_supported_os(self, source_dir, tmp_path):
        cases = [("windows", "x86_64"), ("linux", "x86_64"), ("mac", "arm64")]
        for target_os, arch in cases:
            output = str(tmp_path / f"{target_os}-zip")
            cfg = base_cfg(source_dir, output, target_os=target_os, arch=arch, target_type="zip")
            result = build_zip(cfg)
            assert result.endswith(".zip")
            assert os.path.isfile(result)

    def test_zip_contents(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_type="zip")
        result = build_zip(cfg)
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            assert any("hello.txt" in name for name in names)
            assert any("nested.txt" in name for name in names)

    def test_zip_preserves_empty_directory(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "file.txt").write_text("data")
        (src / "emptydir").mkdir()
        cfg = base_cfg(str(src), str(tmp_path / "out"), target_type="zip")
        result = build_zip(cfg)
        with zipfile.ZipFile(result) as zf:
            assert any("emptydir" in name for name in zf.namelist())

    def test_zip_mac_notarization_submits_without_stapling(self, tmp_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        patch_run("easy_installer.builders.mac_support")

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
            mac_sign_identity="Developer ID Application: Example",
            mac_notary_keychain_profile="notary-profile",
        )
        build_zip(cfg)

        assert any(call["args"][:3] == ["xcrun", "notarytool", "submit"] for call in calls)
        assert not any(call["args"][:3] == ["xcrun", "stapler", "staple"] for call in calls)