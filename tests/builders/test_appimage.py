from __future__ import annotations

import os
from pathlib import Path

import pytest

from easy_installer.builders import _appimage_arch, _host_arch, build_appimage

from tests.conftest import base_cfg


class TestBuildAppImage:
    def test_requires_exec(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_type="appimage")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_appimage(cfg)

    def test_builds_appdir_and_uses_mapped_arch(self, source_dir, output_path, monkeypatch, command_spy):
        calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def inspect_appdir(args, kwargs):
            appdir = Path(args[1])
            captured["apprun"] = (appdir / "AppRun").read_text()
            captured["desktop"] = (appdir / f"TestApp.desktop").read_text()
            captured["arch"] = kwargs["env"]["ARCH"]

        patch_run("easy_installer.builders.appimage", side_effect=inspect_appdir)
        monkeypatch.setattr("easy_installer.builders.appimage.shutil.which", lambda command: "/mock/appimagetool")

        real_isfile = os.path.isfile
        real_access = os.access
        monkeypatch.setattr(
            "easy_installer.builders.appimage.os.path.isfile",
            lambda path: True if path == "/mock/appimagetool" else real_isfile(path),
        )
        monkeypatch.setattr(
            "easy_installer.builders.appimage.os.access",
            lambda path, mode: True if path == "/mock/appimagetool" else real_access(path, mode),
        )

        cfg = base_cfg(
            source_dir,
            output_path,
            target_type="appimage",
            arch="arm64",
            app_name="TestApp",
            app_exec="myapp",
        )
        result = build_appimage(cfg)

        assert result.endswith(".AppImage")
        assert captured["arch"] == "aarch64"
        assert "Exec=myapp" in captured["desktop"]
        assert "usr/bin/myapp" in captured["apprun"]


class TestAppImageMappings:
    def test_arch_mappings(self):
        assert _appimage_arch("x86_64") == "x86_64"
        assert _appimage_arch("arm64") == "aarch64"
        assert _appimage_arch("i386") == "i686"
        assert _appimage_arch("armhf") == "armhf"

    def test_host_arch_returns_string(self):
        result = _host_arch()
        assert isinstance(result, str)
        assert result