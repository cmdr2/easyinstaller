from __future__ import annotations

import pathlib

from easyinstaller.builders import build_nsis

from tests.conftest import base_cfg


class TestBuildNsis:
    def test_generates_script_with_subdir_cleanup(self, tmp_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy

        captured = {}

        def inspect_script(args, _kwargs):
            script_path = pathlib.Path(args[1])
            captured["script"] = script_path.read_text()

        patch_run("easyinstaller.builders.nsis", side_effect=inspect_script)

        src = tmp_path / "src"
        src.mkdir()
        (src / "root.txt").write_text("r")
        deep = src / "sub" / "deep"
        deep.mkdir(parents=True)
        (deep / "inner.txt").write_text("i")

        cfg = base_cfg(str(src), str(tmp_path / "setup"), target_os="windows", target_type="nsis")
        result = build_nsis(cfg)

        script = captured["script"]
        assert result.endswith(".exe")
        assert 'RMDir "$INSTDIR\\sub\\deep"' in script
        assert 'RMDir "$INSTDIR\\sub"' in script
        assert script.index('RMDir "$INSTDIR\\sub\\deep"') < script.index('RMDir "$INSTDIR\\sub"')
        assert any(call["args"][0] == "makensis" for call in calls)

    def test_generated_script_omits_finish_page_run_without_app_exec(self, tmp_path, command_spy):
        _calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def inspect_script(args, _kwargs):
            captured["script"] = pathlib.Path(args[1]).read_text()

        patch_run("easyinstaller.builders.nsis", side_effect=inspect_script)

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.exe").write_text("binary")

        cfg = base_cfg(str(src), str(tmp_path / "setup"), target_os="windows", target_type="nsis")
        build_nsis(cfg)

        assert "!define MUI_FINISHPAGE_RUN " not in captured["script"]
        assert "!define MUI_FINISHPAGE_RUN_TEXT " not in captured["script"]

    def test_generated_script_supports_silent_install_switches(self, tmp_path, command_spy):
        _calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def inspect_script(args, _kwargs):
            captured["script"] = pathlib.Path(args[1]).read_text()

        patch_run("easyinstaller.builders.nsis", side_effect=inspect_script)

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.exe").write_text("binary")

        cfg = base_cfg(str(src), str(tmp_path / "setup"), target_os="windows", target_type="nsis")
        build_nsis(cfg)

        assert "SilentInstall normal" in captured["script"]
        assert "SilentUnInstall normal" in captured["script"]

    def test_generated_script_enables_unicode_and_lzma(self, tmp_path, command_spy):
        _calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def inspect_script(args, _kwargs):
            captured["script"] = pathlib.Path(args[1]).read_text()

        patch_run("easyinstaller.builders.nsis", side_effect=inspect_script)

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.exe").write_text("binary")

        cfg = base_cfg(str(src), str(tmp_path / "setup"), target_os="windows", target_type="nsis")
        build_nsis(cfg)

        assert "Unicode True" in captured["script"]
        assert "SetCompressor /FINAL lzma" in captured["script"]

    def test_generated_script_uses_per_user_install_scope(self, tmp_path, command_spy):
        _calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def inspect_script(args, _kwargs):
            captured["script"] = pathlib.Path(args[1]).read_text()

        patch_run("easyinstaller.builders.nsis", side_effect=inspect_script)

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.exe").write_text("binary")

        cfg = base_cfg(str(src), str(tmp_path / "setup"), target_os="windows", target_type="nsis")
        build_nsis(cfg)

        assert 'InstallDir "$LOCALAPPDATA\\Programs\\setup"' in captured["script"]
        assert "RequestExecutionLevel user" in captured["script"]
        assert "RequestExecutionLevel admin" not in captured["script"]
        assert 'WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\setup"' in captured["script"]
        assert (
            'DeleteRegKey HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\setup"' in captured["script"]
        )
        assert "SetShellVarContext current" in captured["script"]

    def test_generated_script_includes_nested_file_deletes(self, tmp_path, command_spy):
        _calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def inspect_script(args, _kwargs):
            captured["script"] = pathlib.Path(args[1]).read_text()

        patch_run("easyinstaller.builders.nsis", side_effect=inspect_script)

        src = tmp_path / "src"
        src.mkdir()
        nested = src / "sub" / "deep"
        nested.mkdir(parents=True)
        (nested / "inner.txt").write_text("i")

        cfg = base_cfg(str(src), str(tmp_path / "setup"), target_os="windows", target_type="nsis")
        build_nsis(cfg)

        assert 'Delete "$INSTDIR\\sub\\deep\\inner.txt"' in captured["script"]

    def test_escapes_display_name_and_sanitises_install_paths(self, tmp_path, command_spy):
        _calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def inspect_script(args, _kwargs):
            captured["script"] = pathlib.Path(args[1]).read_text()

        patch_run("easyinstaller.builders.nsis", side_effect=inspect_script)

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.exe").write_text("binary")

        cfg = base_cfg(
            str(src),
            str(tmp_path / "setup"),
            target_os="windows",
            target_type="nsis",
            app_name='My "Quoted" App\\Suite',
            app_version='1.0"beta',
        )
        build_nsis(cfg)

        assert 'Name "My $\\"Quoted$\\" App\\Suite"' in captured["script"]
        assert "InstallDir \"$LOCALAPPDATA\\Programs\\My 'Quoted' App-Suite\"" in captured["script"]
        assert (
            'WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\My \'Quoted\' App-Suite" "DisplayName" "My $\\"Quoted$\\" App\\Suite"'
            in captured["script"]
        )
        assert (
            'WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\My \'Quoted\' App-Suite" "DisplayVersion" "1.0$\\"beta"'
            in captured["script"]
        )

    def test_generated_script_adds_finish_page_run_for_app_exec(self, tmp_path, command_spy):
        _calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def inspect_script(args, _kwargs):
            captured["script"] = pathlib.Path(args[1]).read_text()

        patch_run("easyinstaller.builders.nsis", side_effect=inspect_script)

        src = tmp_path / "src"
        nested_dir = src / "bin"
        nested_dir.mkdir(parents=True)
        (nested_dir / "myapp.exe").write_text("binary")

        cfg = base_cfg(
            str(src),
            str(tmp_path / "setup"),
            target_os="windows",
            target_type="nsis",
            app_name="My App",
            app_exec="bin/myapp.exe",
        )
        build_nsis(cfg)

        assert '!define MUI_FINISHPAGE_RUN "$INSTDIR\\bin\\myapp.exe"' in captured["script"]
        assert '!define MUI_FINISHPAGE_RUN_TEXT "Launch My App"' in captured["script"]
        assert "!define MUI_FINISHPAGE_SHOWREADME" in captured["script"]
        assert '!define MUI_FINISHPAGE_SHOWREADME_TEXT "Create a desktop shortcut"' in captured["script"]
        assert "!define MUI_FINISHPAGE_SHOWREADME_FUNCTION easyinstallerCreateDesktopShortcut" in captured["script"]
        assert "Function easyinstallerCreateDesktopShortcut" in captured["script"]
        assert 'CreateShortcut "$DESKTOP\\My App.lnk" "$INSTDIR\\bin\\myapp.exe"' in captured["script"]
        assert 'Delete "$DESKTOP\\My App.lnk"' in captured["script"]
