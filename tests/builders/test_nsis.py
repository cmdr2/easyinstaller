from __future__ import annotations

import pathlib

from easy_installer.builders import build_nsis

from tests.conftest import base_cfg


class TestBuildNsis:
    def test_generates_script_with_subdir_cleanup(self, tmp_path, command_spy):
        calls, patch_run, _patch_subprocess = command_spy

        captured = {}

        def inspect_script(args, _kwargs):
            script_path = pathlib.Path(args[1])
            captured["script"] = script_path.read_text()

        patch_run("easy_installer.builders.nsis", side_effect=inspect_script)

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

    def test_generated_script_includes_nested_file_deletes(self, tmp_path, command_spy):
        _calls, patch_run, _patch_subprocess = command_spy
        captured = {}

        def inspect_script(args, _kwargs):
            captured["script"] = pathlib.Path(args[1]).read_text()

        patch_run("easy_installer.builders.nsis", side_effect=inspect_script)

        src = tmp_path / "src"
        src.mkdir()
        nested = src / "sub" / "deep"
        nested.mkdir(parents=True)
        (nested / "inner.txt").write_text("i")

        cfg = base_cfg(str(src), str(tmp_path / "setup"), target_os="windows", target_type="nsis")
        build_nsis(cfg)

        assert 'Delete "$INSTDIR\\sub\\deep\\inner.txt"' in captured["script"]
