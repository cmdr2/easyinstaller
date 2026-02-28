# easy-installer

Create installers and archives from a release folder for any target OS.

Give it a folder, pick a target platform and format, and it produces the package — zip, tar.gz, deb, rpm, AppImage, Flatpak, Snap, NSIS installer, DMG, or macOS .app bundle.

## Supported targets

| OS      | Types                                              |
|---------|----------------------------------------------------|
| Windows | `zip`, `tar.gz`, `nsis`                            |
| Linux   | `zip`, `tar.gz`, `deb`, `rpm`, `appimage`, `flatpak`, `snap` |
| Mac     | `zip`, `tar.gz`, `dmg`, `app`                      |

## Installation

```bash
pip install .
```

## Usage

```
easy-installer --source <dir> --os <os> --arch <arch> --type <type> --output <name> [options]
```

### Required arguments

| Flag       | Description                                              |
|------------|----------------------------------------------------------|
| `--source` | Path to the release folder to package                    |
| `--os`     | Target OS: `windows` (or `win`), `linux`, `mac` (or `macos`/`osx`) |
| `--arch`   | Architecture: `x86_64`, `arm64`, `i386`, `armhf` (plus aliases like `amd64`, `aarch64`) |
| `--type`   | Package type (see table above)                           |
| `--output` | Output file name **without** extension                   |

### Optional metadata

| Flag                | Default                                | Used by                            |
|---------------------|----------------------------------------|------------------------------------|
| `--app-name`        | basename of `--output`                 | deb, rpm, nsis, appimage, flatpak, snap, dmg, app |
| `--app-version`     | `1.0.0`                                | all installer types                |
| `--app-description` | `Application packaged with easy-installer` | deb, rpm, snap                 |
| `--app-maintainer`  | `maintainer@example.com`               | deb                                |
| `--app-category`    | `Utility`                              | deb, appimage                      |
| `--app-exec`        | *(none)*                               | appimage, flatpak, snap, app (**required**) |
| `--app-icon`        | *(none)*                               | appimage, app                      |

### Examples

```bash
# Create a .tar.gz for Linux
easy-installer --source ./build --os linux --arch x86_64 --type tar.gz \
    --output myapp-1.0.0-linux-x64

# Create a .deb package
easy-installer --source ./build --os linux --arch x86_64 --type deb \
    --output myapp \
    --app-name "My App" --app-version 1.0.0 --app-exec myapp

# Create a macOS .app bundle
easy-installer --source ./build --os mac --arch arm64 --type app \
    --output MyApp \
    --app-name "My App" --app-exec myapp

# Create a Windows NSIS installer (requires makensis)
easy-installer --source ./build --os windows --arch x86_64 --type nsis \
    --output myapp-setup \
    --app-name "My App" --app-version 1.0.0
```

## External dependencies

The archive types (`zip`, `tar.gz`) and `.app` bundles are built with pure Python — no external tools needed.

Other formats require the corresponding tool to be installed on the build machine:

| Type       | Requires          |
|------------|-------------------|
| `nsis`     | `makensis`        |
| `deb`      | `dpkg-deb`        |
| `rpm`      | `rpmbuild`        |
| `appimage` | `appimagetool` (auto-downloaded if missing) |
| `flatpak`  | `flatpak`, `flatpak-builder` |
| `snap`     | `snapcraft`       |
| `dmg`      | `hdiutil` (macOS) |

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## License

MIT
