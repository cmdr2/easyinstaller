from __future__ import annotations

from pathlib import Path

from easyinstaller.builders import build_deb

from tests.conftest import base_cfg


class TestBuildDeb:
    def test_writes_control_file_and_symlink(self, source_dir, output_path, command_spy, monkeypatch):
        calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def fake_symlink(target, link_name):
            captured["symlink"] = target
            Path(link_name).write_text(f"symlink -> {target}")

        def inspect_deb_root(args, _kwargs):
            deb_root = Path(args[3])
            captured["control"] = (deb_root / "DEBIAN" / "control").read_text()
            Path(args[4]).write_text("fake deb")

        patch_run("easyinstaller.builders.deb", side_effect=inspect_deb_root)
        monkeypatch.setattr("easyinstaller.builders.deb.os.symlink", fake_symlink)

        cfg = base_cfg(
            source_dir,
            output_path,
            target_type="deb",
            app_name="My Spaced App",
            app_version="2.0.0",
            app_exec="myapp",
        )
        result = build_deb(cfg)

        assert result.endswith(".deb")
        assert "Architecture: amd64" in captured["control"]
        assert "Package: my-spaced-app" in captured["control"]
        assert captured["symlink"] == "/opt/my-spaced-app/myapp"
        assert any(call["args"][0] == "dpkg-deb" for call in calls)

    def test_nested_app_exec_symlinks_by_basename(self, tmp_path, output_path, command_spy, monkeypatch):
        calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        source = tmp_path / "source"
        nested = source / "bin"
        nested.mkdir(parents=True)
        (nested / "myapp").write_text("#!/bin/sh\nexit 0\n")

        def fake_symlink(target, link_name):
            captured["symlink"] = target
            captured["link_name"] = Path(link_name)
            captured["link_name"].write_text(f"symlink -> {target}")

        def inspect_deb_root(args, _kwargs):
            Path(args[4]).write_text("fake deb")

        patch_run("easyinstaller.builders.deb", side_effect=inspect_deb_root)
        monkeypatch.setattr("easyinstaller.builders.deb.os.symlink", fake_symlink)

        cfg = base_cfg(
            str(source),
            output_path,
            target_type="deb",
            app_name="Nested App",
            app_exec="bin/myapp",
        )
        build_deb(cfg)

        assert captured["symlink"] == "/opt/nested-app/bin/myapp"
        assert captured["link_name"].name == "myapp"
        assert any(call["args"][0] == "dpkg-deb" for call in calls)
