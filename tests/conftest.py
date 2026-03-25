from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from easyinstaller.config import Config, validate_and_normalise


@pytest.fixture()
def source_dir(tmp_path):
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
    return str(tmp_path / "output")


def base_cfg(source_dir: str, output: str, **overrides) -> Config:
    defaults = dict(
        source=source_dir,
        target_os="linux",
        arch="x86_64",
        target_type="zip",
        output=output,
    )
    defaults.update(overrides)
    return validate_and_normalise(Config(**defaults))


@pytest.fixture()
def command_spy(monkeypatch):
    calls: list[dict[str, object]] = []

    def patch_run(module_path: str, side_effect=None):
        monkeypatch.setattr(f"{module_path}._require", lambda command: f"/mock/{command}", raising=False)

        def fake_run(args, **kwargs):
            calls.append({"kind": "run", "module": module_path, "args": args, "kwargs": kwargs})
            if side_effect is not None:
                side_effect(args, kwargs)
            return SimpleNamespace(args=args, returncode=0)

        monkeypatch.setattr(f"{module_path}._run", fake_run, raising=False)

    def patch_subprocess(module_path: str, side_effect=None):
        def fake_subprocess_run(args, **kwargs):
            calls.append({"kind": "subprocess", "module": module_path, "args": args, "kwargs": kwargs})
            if side_effect is not None:
                side_effect(args, kwargs)
            return SimpleNamespace(args=args, returncode=0)

        monkeypatch.setattr(f"{module_path}.subprocess.run", fake_subprocess_run, raising=False)

    return calls, patch_run, patch_subprocess
