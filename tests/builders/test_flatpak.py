from __future__ import annotations

from pathlib import Path

import pytest

from easyinstaller.builders import _flatpak_arch, build_flatpak

from tests.conftest import base_cfg


class TestBuildFlatpak:
    def test_requires_exec(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_type="flatpak")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_flatpak(cfg)

    def test_builds_manifest_and_runs_expected_commands(self, source_dir, output_path, command_spy):
        calls, patch_run, patch_subprocess = command_spy
        captured = {}

        def inspect_manifest(args, _kwargs):
            if args[0] == "flatpak-builder":
                manifest_path = Path(args[-1])
                captured["manifest"] = manifest_path.read_text()

        patch_run("easyinstaller.builders.flatpak", side_effect=inspect_manifest)
        patch_subprocess("easyinstaller.builders.flatpak")

        cfg = base_cfg(
            source_dir,
            output_path,
            target_type="flatpak",
            arch="arm64",
            app_name="TestApp",
            app_exec="myapp",
        )
        result = build_flatpak(cfg)

        assert result.endswith(".flatpak")
        assert '"command": "myapp"' in captured["manifest"]
        assert '"runtime-version": "24.08"' in captured["manifest"]
        assert any(call["kind"] == "subprocess" and call["args"][0] == "flatpak" for call in calls)
        assert any(
            call["kind"] == "run"
            and call["args"][:4] == ["flatpak-builder", "--user", "--force-clean", "--arch"]
            and call["args"][4] == "aarch64"
            for call in calls
        )


class TestFlatpakMappings:
    def test_arch_mappings(self):
        assert _flatpak_arch("x86_64") == "x86_64"
        assert _flatpak_arch("arm64") == "aarch64"
        assert _flatpak_arch("i386") == "i386"
        assert _flatpak_arch("armhf") == "arm"
