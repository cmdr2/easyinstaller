from __future__ import annotations

import os

import pytest

from easyinstaller.config import ConfigError

from .conftest import base_cfg


class TestValidation:
    def test_valid_config(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path)
        assert cfg.target_os == "linux"
        assert cfg.arch == "x86_64"
        assert cfg.target_type == "zip"

    def test_supports_app_in_dmg_target(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app-in-dmg", arch="arm64")
        assert cfg.target_type == "app-in-dmg"

    def test_supports_pkg_targets(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="pkg", arch="arm64")
        assert cfg.target_type == "pkg"

        cfg = base_cfg(source_dir, output_path, target_os="mac", target_type="app-in-pkg", arch="arm64")
        assert cfg.target_type == "app-in-pkg"

    def test_os_aliases(self, source_dir, output_path):
        for alias, expected in [("win", "windows"), ("macos", "mac"), ("osx", "mac")]:
            cfg = base_cfg(source_dir, output_path, target_os=alias)
            assert cfg.target_os == expected

    def test_type_aliases(self, source_dir, output_path):
        for alias, expected in [("targz", "tar.gz"), ("tgz", "tar.gz")]:
            cfg = base_cfg(source_dir, output_path, target_type=alias)
            assert cfg.target_type == expected

    def test_invalid_os(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="Unsupported OS"):
            base_cfg(source_dir, output_path, target_os="bsd")

    def test_invalid_arch(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="Unsupported arch"):
            base_cfg(source_dir, output_path, arch="amd64")

    def test_mac_notarize_requires_mac_target(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="only supported for mac targets"):
            base_cfg(
                source_dir,
                output_path,
                target_os="linux",
                target_type="zip",
                mac_notarize=True,
                mac_notary_team_name="Example, Inc.",
                mac_notary_team_id="TEAMID1234",
                mac_notary_keychain_profile="notary-profile",
            )

    def test_mac_notarize_requires_team_name(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="requires --mac-notary-team-name"):
            base_cfg(
                source_dir,
                output_path,
                target_os="mac",
                target_type="zip",
                arch="arm64",
                mac_notarize=True,
                mac_notary_team_id="TEAMID1234",
                mac_notary_keychain_profile="notary-profile",
            )

    def test_mac_notarize_requires_team_id(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="requires --mac-notary-team-id"):
            base_cfg(
                source_dir,
                output_path,
                target_os="mac",
                target_type="zip",
                arch="arm64",
                mac_notarize=True,
                mac_notary_team_name="Example, Inc.",
                mac_notary_keychain_profile="notary-profile",
            )

    def test_mac_notarize_requires_credentials(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="requires either --mac-notary-keychain-profile"):
            base_cfg(
                source_dir,
                output_path,
                target_os="mac",
                target_type="zip",
                arch="arm64",
                mac_notarize=True,
                mac_notary_team_name="Example, Inc.",
                mac_notary_team_id="TEAMID1234",
            )

    def test_mac_notarize_rejects_tar_gz(self, source_dir, output_path):
        with pytest.raises(
            ConfigError, match="only supported for mac types: zip, dmg, app, app-in-dmg, pkg, app-in-pkg"
        ):
            base_cfg(
                source_dir,
                output_path,
                target_os="mac",
                target_type="tar.gz",
                arch="arm64",
                mac_notarize=True,
                mac_notary_team_name="Example, Inc.",
                mac_notary_team_id="TEAMID1234",
                mac_notary_keychain_profile="notary-profile",
            )

    def test_invalid_type(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="Unsupported type"):
            base_cfg(source_dir, output_path, target_type="msi")

    def test_invalid_os_type_combo(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="not supported for windows"):
            base_cfg(source_dir, output_path, target_os="windows", target_type="deb")

    def test_missing_source_dir(self, output_path):
        with pytest.raises(ConfigError, match="does not exist"):
            base_cfg("/nonexistent/path", output_path)

    def test_app_name_defaults_to_output_basename(self, source_dir, output_path):
        cfg = base_cfg(source_dir, output_path)
        assert cfg.app_name == os.path.basename(output_path)

    def test_output_resolved_to_absolute(self, source_dir):
        cfg = base_cfg(source_dir, "relative-output")
        assert os.path.isabs(cfg.output)

    def test_output_folder_path_uses_last_segment_as_filename(self, source_dir, tmp_path):
        cfg = base_cfg(source_dir, str(tmp_path / "artifacts" / "release") + os.sep)
        assert cfg.output.endswith(os.path.join("artifacts", "release", "release"))

    def test_app_exec_allows_relative_subpath(self, output_path, tmp_path):
        source = tmp_path / "source"
        nested = source / "bin"
        nested.mkdir(parents=True)
        (nested / "myapp").write_text("#!/bin/bash\nexit 0\n")

        cfg = base_cfg(str(source), output_path, app_exec="bin/myapp")
        assert cfg.app_exec == "bin/myapp"

    def test_app_exec_must_not_escape_source_directory(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="must stay inside the source directory"):
            base_cfg(source_dir, output_path, app_exec="../myapp")

    def test_app_exec_must_exist_in_source_directory(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="does not exist"):
            base_cfg(source_dir, output_path, app_exec="missing")
