# easyinstaller

Create installers and archives from a release folder for any target OS.

Give it a folder, pick a target platform and format, and it produces the package - zip, tar.gz, deb, rpm, AppImage, Flatpak, Snap, NSIS installer, DMG, a macOS .app bundle, or a DMG containing a .app bundle.

## Supported targets

| OS      | Types                                              |
|---------|----------------------------------------------------|
| Windows | `zip`, `tar.gz`, `nsis`                            |
| Linux   | `zip`, `tar.gz`, `deb`, `rpm`, `appimage`, `flatpak`, `snap` |
| Mac     | `zip`, `tar.gz`, `dmg`, `app`, `app-in-dmg`        |

## Installation

```bash
pip install .
```

## Usage

```
easyinstaller --source <dir> --os <os> --arch <arch> --type <type> --output <name> [options]
```

See [docs/cli.md](docs/cli.md) for the full argument list, notarization flags, and examples.

## Guides
Building installers for:
- [Windows](docs/windows.md)
- [Linux](docs/linux.md)
- [macOS](docs/mac.md)

See [release-example.yml](.github/workflows/release-example.yml) for a minimal GitHub Actions workflow that builds an example project for Windows, Linux, and macOS, and releases installers for it.

### Examples

```bash
# Create a .tar.gz for Linux
easyinstaller --source ./build --os linux --arch x86_64 --type tar.gz \
    --output myapp-1.0.0-linux-x64

# Create a .deb package
easyinstaller --source ./build --os linux --arch x86_64 --type deb \
    --output myapp \
    --app-name "My App" --app-version 1.0.0 --app-exec myapp

# Create a macOS .app bundle
easyinstaller --source ./build --os mac --arch arm64 --type app \
    --output MyApp \
    --app-name "My App" --app-exec myapp

# Create a notarized macOS app-in-dmg build using a notarytool keychain profile
easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg \
    --output MyApp \
    --app-name "My App" --app-exec myapp \
    --mac-notarize \
    --mac-sign-identity "Developer ID Application: Example, Inc. (TEAMID1234)" \
    --mac-notary-keychain-profile my-notary-profile

# Use a folder path for output; this creates dist/release/release.zip
easyinstaller --source ./build --os linux --arch x86_64 --type zip \
    --output dist/release/

# Create a Windows NSIS installer (requires makensis)
easyinstaller --source ./build --os windows --arch x86_64 --type nsis \
    --output myapp-setup \
    --app-name "My App" --app-version 1.0.0
```

## External dependencies

The archive types (`zip`, `tar.gz`) and plain `.app` bundles can be built without additional tools.

Other formats require the corresponding tool to be installed on the build machine:

| Type       | Requires          |
|------------|-------------------|
| `nsis`     | [makensis](https://sourceforge.net/projects/nsis/files/NSIS%203/3.11/nsis-3.11.zip/download) |
| `deb`      | `dpkg-deb`        |
| `rpm`      | `rpmbuild`        |
| `appimage` | `appimagetool`    |
| `flatpak`  | `flatpak`, `flatpak-builder` |
| `snap`     | `snapcraft`       |
| `dmg`      | `hdiutil` (macOS) |
| mac notarization | `codesign`, `xcrun notarytool`, `xcrun stapler` (macOS) |

## Running tests

```bash
pip install pytest
python -m pytest tests/ tests_integration/ -v
```

The integration suite under `tests_integration/` builds real artifacts. Tests that require a specific host OS skip automatically on the wrong host, and tests fail fast when their required external tools are missing on the correct host OS.
