"""Tests for easy-installer."""

from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
import zipfile

import pytest

from easy_installer.config import Config, ConfigError, validate_and_normalise
from easy_installer.builders import build_zip, build_tar_gz, build_app, build_deb, build_rpm
from easy_installer.cli import main


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def source_dir(tmp_path):
    """Create a sample release folder."""
    src = tmp_path / "source"
    src.mkdir()
    (src / "hello.txt").write_text("hello world")
    sub = src / "subdir"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested file")
    app = src / "myapp"
    app.write_text("#!/bin/bash\necho running\n")
    app.chmod(0o755)
    return str(src)


@pytest.fixture()
def output_path(tmp_path):
    """Return a base output path (without extension)."""
    return str(tmp_path / "output")


def _base_cfg(source_dir: str, output: str, **overrides) -> Config:
    defaults = dict(
        source=source_dir,
        target_os="linux",
        arch="x86_64",
        target_type="zip",
        output=output,
    )
    defaults.update(overrides)
    return validate_and_normalise(Config(**defaults))


# ── Config / validation tests ────────────────────────────────────────────────

class TestValidation:
    def test_valid_config(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path)
        assert cfg.target_os == "linux"
        assert cfg.arch == "x86_64"
        assert cfg.target_type == "zip"

    def test_os_aliases(self, source_dir, output_path):
        for alias, expected in [("win", "windows"), ("macos", "mac"), ("osx", "mac")]:
            cfg = _base_cfg(source_dir, output_path, target_os=alias)
            assert cfg.target_os == expected

    def test_arch_aliases(self, source_dir, output_path):
        for alias, expected in [("amd64", "x86_64"), ("x64", "x86_64"), ("aarch64", "arm64")]:
            cfg = _base_cfg(source_dir, output_path, arch=alias)
            assert cfg.arch == expected

    def test_type_aliases(self, source_dir, output_path):
        for alias, expected in [("targz", "tar.gz"), ("tgz", "tar.gz")]:
            cfg = _base_cfg(source_dir, output_path, target_type=alias)
            assert cfg.target_type == expected

    def test_invalid_os(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="Unsupported OS"):
            _base_cfg(source_dir, output_path, target_os="bsd")

    def test_invalid_arch(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="Unsupported arch"):
            _base_cfg(source_dir, output_path, arch="sparc")

    def test_invalid_type(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="Unsupported type"):
            _base_cfg(source_dir, output_path, target_type="msi")

    def test_invalid_os_type_combo(self, source_dir, output_path):
        with pytest.raises(ConfigError, match="not supported for windows"):
            _base_cfg(source_dir, output_path, target_os="windows", target_type="deb")

    def test_missing_source_dir(self, output_path):
        with pytest.raises(ConfigError, match="does not exist"):
            _base_cfg("/nonexistent/path", output_path)

    def test_app_name_defaults_to_output_basename(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path)
        assert cfg.app_name == os.path.basename(output_path)

    def test_output_resolved_to_absolute(self, source_dir):
        cfg = _base_cfg(source_dir, "relative-output")
        assert os.path.isabs(cfg.output)


# ── Builder tests: zip ───────────────────────────────────────────────────────

class TestBuildZip:
    def test_creates_zip(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path, target_type="zip")
        result = build_zip(cfg)
        assert result.endswith(".zip")
        assert os.path.isfile(result)

    def test_zip_contents(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path, target_type="zip")
        result = build_zip(cfg)
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            assert any("hello.txt" in n for n in names)
            assert any("nested.txt" in n for n in names)

    def test_zip_preserves_content(self, source_dir, output_path, tmp_path):
        cfg = _base_cfg(source_dir, output_path, target_type="zip")
        result = build_zip(cfg)
        extract_dir = str(tmp_path / "extract")
        with zipfile.ZipFile(result) as zf:
            zf.extractall(extract_dir)
        # Find hello.txt inside extracted folder
        for dirpath, _, files in os.walk(extract_dir):
            if "hello.txt" in files:
                with open(os.path.join(dirpath, "hello.txt")) as f:
                    content = f.read()
                assert content == "hello world"
                return
        pytest.fail("hello.txt not found in extracted zip")


# ── Builder tests: tar.gz ────────────────────────────────────────────────────

class TestBuildTarGz:
    def test_creates_tar_gz(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path, target_type="tar.gz")
        result = build_tar_gz(cfg)
        assert result.endswith(".tar.gz")
        assert os.path.isfile(result)

    def test_tar_gz_contents(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path, target_type="tar.gz")
        result = build_tar_gz(cfg)
        with tarfile.open(result) as tf:
            names = tf.getnames()
            assert any("hello.txt" in n for n in names)
            assert any("nested.txt" in n for n in names)

    def test_tar_gz_preserves_content(self, source_dir, output_path, tmp_path):
        cfg = _base_cfg(source_dir, output_path, target_type="tar.gz")
        result = build_tar_gz(cfg)
        extract_dir = str(tmp_path / "extract")
        os.makedirs(extract_dir)
        with tarfile.open(result) as tf:
            tf.extractall(extract_dir)
        for dirpath, _, files in os.walk(extract_dir):
            if "hello.txt" in files:
                with open(os.path.join(dirpath, "hello.txt")) as f:
                    content = f.read()
                assert content == "hello world"
                return
        pytest.fail("hello.txt not found in extracted tar.gz")


# ── Builder tests: .app ─────────────────────────────────────────────────────

class TestBuildApp:
    def test_creates_app_bundle(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path, target_os="mac", target_type="app", app_exec="myapp")
        result = build_app(cfg)
        assert result.endswith(".app")
        assert os.path.isdir(result)

    def test_app_structure(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path, target_os="mac", target_type="app", app_exec="myapp")
        result = build_app(cfg)
        assert os.path.isfile(os.path.join(result, "Contents", "Info.plist"))
        assert os.path.isfile(os.path.join(result, "Contents", "MacOS", "myapp"))
        assert os.path.isfile(os.path.join(result, "Contents", "Resources", "hello.txt"))

    def test_info_plist_content(self, source_dir, output_path):
        cfg = _base_cfg(
            source_dir, output_path,
            target_os="mac", target_type="app",
            app_exec="myapp", app_name="TestApp", app_version="1.2.3",
        )
        result = build_app(cfg)
        with open(os.path.join(result, "Contents", "Info.plist")) as f:
            plist = f.read()
        assert "TestApp" in plist
        assert "1.2.3" in plist
        assert "myapp" in plist

    def test_app_requires_exec(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path, target_os="mac", target_type="app")
        with pytest.raises(RuntimeError, match="app-exec is required"):
            build_app(cfg)

    def test_launcher_is_executable(self, source_dir, output_path):
        cfg = _base_cfg(source_dir, output_path, target_os="mac", target_type="app", app_exec="myapp")
        result = build_app(cfg)
        launcher = os.path.join(result, "Contents", "MacOS", "myapp")
        assert os.access(launcher, os.X_OK)


# ── Builder tests: deb ───────────────────────────────────────────────────────

@pytest.mark.skipif(shutil.which("dpkg-deb") is None, reason="dpkg-deb not available")
class TestBuildDeb:
    def test_creates_deb(self, source_dir, output_path):
        cfg = _base_cfg(
            source_dir, output_path, target_type="deb",
            app_name="TestApp", app_version="2.0.0", app_exec="myapp",
        )
        result = build_deb(cfg)
        assert result.endswith(".deb")
        assert os.path.isfile(result)

    def test_deb_metadata(self, source_dir, output_path):
        import subprocess
        cfg = _base_cfg(
            source_dir, output_path, target_type="deb",
            app_name="TestApp", app_version="2.0.0", app_exec="myapp",
            app_maintainer="test@test.com",
        )
        result = build_deb(cfg)
        info = subprocess.check_output(["dpkg-deb", "--info", result], text=True)
        assert "amd64" in info
        assert "2.0.0" in info


# ── Builder tests: rpm ───────────────────────────────────────────────────────

@pytest.mark.skipif(shutil.which("rpmbuild") is None, reason="rpmbuild not available")
class TestBuildRpm:
    def test_creates_rpm(self, source_dir, output_path):
        cfg = _base_cfg(
            source_dir, output_path, target_type="rpm",
            app_name="TestApp", app_version="1.0.0",
        )
        result = build_rpm(cfg)
        assert result.endswith(".rpm")
        assert os.path.isfile(result)


# ── CLI tests ────────────────────────────────────────────────────────────────

class TestCLI:
    def test_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_missing_required(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--source", "/tmp", "--os", "linux", "--arch", "x86_64", "--type", "zip"])
        assert exc_info.value.code == 2

    def test_invalid_os(self, source_dir):
        ret = main(["--source", source_dir, "--os", "bsd", "--arch", "x86_64",
                     "--type", "zip", "--output", "/tmp/test-out"])
        assert ret == 1

    def test_end_to_end_zip(self, source_dir, output_path):
        ret = main(["--source", source_dir, "--os", "linux", "--arch", "x86_64",
                     "--type", "zip", "--output", output_path])
        assert ret == 0
        assert os.path.isfile(output_path + ".zip")

    def test_end_to_end_tar_gz(self, source_dir, output_path):
        ret = main(["--source", source_dir, "--os", "linux", "--arch", "x86_64",
                     "--type", "tar.gz", "--output", output_path])
        assert ret == 0
        assert os.path.isfile(output_path + ".tar.gz")

    def test_end_to_end_app(self, source_dir, output_path):
        ret = main(["--source", source_dir, "--os", "mac", "--arch", "arm64",
                     "--type", "app", "--output", output_path,
                     "--app-name", "TestApp", "--app-exec", "myapp"])
        assert ret == 0
        assert os.path.isdir(output_path + ".app")
