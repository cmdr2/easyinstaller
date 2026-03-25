# easyinstaller

Create installers and archives from a release folder for any target OS.

Give it a folder, pick a target platform and format, and it produces the package — zip, tar.gz, deb, rpm, AppImage, Flatpak, Snap, NSIS installer, DMG, a macOS .app bundle, or a DMG containing a .app bundle.

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

### Required arguments

| Flag       | Description                                              |
|------------|----------------------------------------------------------|
| `--source` | Path to the release folder to package                    |
| `--os`     | Target OS: `windows` (or `win`), `linux`, `mac` (or `macos`/`osx`) |
| `--arch`   | Architecture: `x86_64`, `arm64`, `i386`, or `armhf`     |
| `--type`   | Package type (see table above)                           |
| `--output` | Output file name **without** extension, or a folder path whose last segment becomes the file name |

### Optional metadata

| Flag                | Default                                | Used by                            |
|---------------------|----------------------------------------|------------------------------------|
| `--app-name`        | basename of `--output`                 | deb, rpm, nsis, appimage, flatpak, snap, dmg, app |
| `--app-version`     | `1.0.0`                                | all installer types                |
| `--app-description` | `Application packaged with easyinstaller` | deb, rpm, snap                 |
| `--app-maintainer`  | `maintainer@example.com`               | deb                                |
| `--app-category`    | `Utility`                              | deb, appimage                      |
| `--app-exec`        | *(none)*                               | appimage, flatpak, snap, app, app-in-dmg (**required**; must stay within the source tree) |
| `--app-icon`        | *(none)*                               | appimage, app                      |

### Mac notarization options

Use these options with mac targets when you want easyinstaller to sign copied binaries in a staging folder, submit the final output to Apple notarization, and staple where supported.

| Flag                           | Default  | Notes |
|--------------------------------|----------|-------|
| `--mac-notarize`               | off      | Enables signing and notarization for mac targets |
| `--mac-sign-identity`          | *(none)* | Required with `--mac-notarize`; Developer ID Application identity used by `codesign` |
| `--mac-notary-keychain-profile`| *(none)* | Preferred `notarytool` authentication method |
| `--mac-notary-apple-id`        | *(none)* | Use with direct credentials if no keychain profile is configured |
| `--mac-notary-team-id`         | *(none)* | Use with direct credentials if no keychain profile is configured |
| `--mac-notary-password`        | *(none)* | Use with direct credentials if no keychain profile is configured |

When notarization is enabled for mac targets, easyinstaller copies the source into a staging folder, recursively signs `.dylib` files and executable binaries there, builds the target from that staged content, submits the output with `xcrun notarytool submit --wait`, and then staples the result when Apple supports stapling for that format.

The accepted architecture names are fixed: `x86_64`, `arm64`, `i386`, and `armhf`. easyinstaller maps those names internally for tools that expect different architecture strings.

If `--output` points to a folder path, easyinstaller uses the last path segment as the base file name. For example, `--output dist/release/` creates `dist/release/release.zip` for the `zip` target.

Stapling behavior by mac target:

| Type         | Submitted for notarization | Stapled |
|--------------|----------------------------|---------|
| `zip`        | Yes                        | No      |
| `tar.gz`     | Yes                        | No      |
| `app`        | Yes                        | Yes, to the `.app` |
| `dmg`        | Yes                        | Yes, to the `.dmg` |
| `app-in-dmg` | Yes                        | Yes, to the `.dmg` |

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

The archive types (`zip`, `tar.gz`) and plain `.app` bundles are built with pure Python when notarization is not enabled.

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
| mac notarization | `codesign`, `xcrun notarytool`, `xcrun stapler` (macOS) |

## Running tests

```bash
pip install pytest
python -m pytest tests/ tests_integration/ -v
```

The integration suite under `tests_integration/` builds real artifacts. Tests that depend on platform-specific tooling skip automatically when they are run on the wrong host OS or when the required tool is unavailable.
