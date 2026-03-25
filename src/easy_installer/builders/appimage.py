"""AppImage builder."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import urllib.request

from ..config import Config
from .common import _appimage_arch, _host_arch, _run, log


def build_appimage(cfg: Config) -> str:
    if not cfg.app_exec:
        raise RuntimeError("--app-exec is required for AppImage")

    output_file = cfg.output + ".AppImage"
    log.info("Creating AppImage: %s", output_file)

    appdir = tempfile.mkdtemp(prefix="easyinstaller-appimage-")
    try:
        usr_bin = os.path.join(appdir, "usr", "bin")
        os.makedirs(usr_bin)
        shutil.copytree(cfg.source, usr_bin, dirs_exist_ok=True)

        desktop_dir = os.path.join(appdir, "usr", "share", "applications")
        icon_dir = os.path.join(appdir, "usr", "share", "icons", "hicolor", "256x256", "apps")
        os.makedirs(desktop_dir)
        os.makedirs(icon_dir)

        desktop = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={cfg.app_name}\n"
            f"Exec={cfg.app_exec}\n"
            f"Icon={cfg.app_name}\n"
            f"Categories={cfg.app_category};\n"
        )
        with open(os.path.join(appdir, f"{cfg.app_name}.desktop"), "w") as handle:
            handle.write(desktop)
        with open(os.path.join(desktop_dir, f"{cfg.app_name}.desktop"), "w") as handle:
            handle.write(desktop)

        if cfg.app_icon and os.path.isfile(cfg.app_icon):
            shutil.copy2(cfg.app_icon, os.path.join(appdir, f"{cfg.app_name}.png"))
            shutil.copy2(cfg.app_icon, os.path.join(icon_dir, f"{cfg.app_name}.png"))
        else:
            import base64

            pixel = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
                "2mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            )
            for path in (
                os.path.join(appdir, f"{cfg.app_name}.png"),
                os.path.join(icon_dir, f"{cfg.app_name}.png"),
            ):
                with open(path, "wb") as handle:
                    handle.write(pixel)

        apprun = os.path.join(appdir, "AppRun")
        with open(apprun, "w") as handle:
            handle.write(
                "#!/bin/bash\n"
                'SELF="$(readlink -f "$0")"\n'
                'HERE="$(dirname "$SELF")"\n'
                'export PATH="${HERE}/usr/bin:${PATH}"\n'
                'export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"\n'
                f'exec "${{HERE}}/usr/bin/{cfg.app_exec}" "$@"\n'
            )
        os.chmod(apprun, 0o755)

        appimagetool = shutil.which("appimagetool") or "/tmp/appimagetool"
        if not os.path.isfile(appimagetool) or not os.access(appimagetool, os.X_OK):
            host_arch = _host_arch()
            url = (
                "https://github.com/AppImage/appimagetool/releases/"
                f"download/continuous/appimagetool-{host_arch}.AppImage"
            )
            log.info("Downloading appimagetool from %s", url)
            urllib.request.urlretrieve(url, appimagetool)
            os.chmod(appimagetool, 0o755)

        env = {**os.environ, "ARCH": _appimage_arch(cfg.arch)}
        try:
            _run([appimagetool, appdir, output_file], env=env)
        except subprocess.CalledProcessError:
            _run([appimagetool, "--appimage-extract-and-run", appdir, output_file], env=env)
    finally:
        shutil.rmtree(appdir, ignore_errors=True)

    log.info("Created: %s", output_file)
    return output_file