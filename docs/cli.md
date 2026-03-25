# CLI reference

## Usage

```bash
easyinstaller --source <dir> --os <os> --arch <arch> --type <type> --output <name> [options]
```


## Required arguments

| Flag | Description |
|------|-------------|
| `--source` | Path to the release folder to package |
| `--os` | Target OS: `windows` (or `win`), `linux`, `mac` (or `macos` or `osx`) |
| `--arch` | Architecture: `x86_64`, `arm64`, `i386`, or `armhf` |
| `--type` | Package type for the selected OS |
| `--output` | Output file name without extension, or a folder path whose last segment becomes the file name |

## Optional metadata

| Flag | Default | Used by |
|------|---------|---------|
| `--app-name` | basename of `--output` | deb, rpm, nsis, appimage, flatpak, snap, dmg, app |
| `--app-version` | `1.0.0` | all installer types |
| `--app-description` | `Application packaged with easyinstaller` | deb, rpm, snap |
| `--app-maintainer` | `maintainer@example.com` | deb |
| `--app-category` | `Utility` | deb, appimage |
| `--app-exec` | none | nsis, appimage, flatpak, snap, app, app-in-dmg. Optional for nsis; required for the other listed targets and must stay inside the source tree |
| `--app-icon` | none | appimage, app |

## mac notarization flags

| Flag | Default | Notes |
|------|---------|-------|
| `--mac-notarize` | off | Enables signing and notarization for mac targets |
| `--mac-sign-identity` | none | Required with `--mac-notarize`; Developer ID Application identity used by `codesign` |
| `--mac-notary-keychain-profile` | none | Name of a `notarytool` keychain profile created with `xcrun notarytool store-credentials` |
| `--mac-notary-apple-id` | none | Use with direct credentials if no keychain profile is configured |
| `--mac-notary-team-id` | none | Use with direct credentials if no keychain profile is configured |
| `--mac-notary-password` | none | Use with direct credentials if no keychain profile is configured |

When notarization is enabled, easyinstaller copies the source into a staging folder, signs copied binaries there, submits the final output with `xcrun notarytool submit --wait`, and staples the result when Apple supports stapling for that format.

## Notes

| Topic | Detail |
|-------|--------|
| Supported Windows types | `zip`, `tar.gz`, `nsis` |
| Supported Linux types | `zip`, `tar.gz`, `deb`, `rpm`, `appimage`, `flatpak`, `snap` |
| Supported Mac types | `zip`, `tar.gz`, `dmg`, `app`, `app-in-dmg` |
| Accepted arch names | `x86_64`, `arm64`, `i386`, `armhf` |
| Output folders | `--output dist/release/` creates `dist/release/release.<ext>` |
| Stapled mac targets | `app`, `dmg`, `app-in-dmg` |
| Submitted but not stapled | `zip`, `tar.gz` |

## Examples

```bash
# Linux tar.gz
easyinstaller --source ./build --os linux --arch x86_64 --type tar.gz \
    --output myapp-1.0.0-linux-x64

# Linux deb
easyinstaller --source ./build --os linux --arch x86_64 --type deb \
    --output myapp \
    --app-name "My App" --app-version 1.0.0 --app-exec myapp

# macOS app
easyinstaller --source ./build --os mac --arch arm64 --type app \
    --output MyApp \
    --app-name "My App" --app-exec myapp

# notarized macOS app-in-dmg
easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg \
    --output MyApp \
    --app-name "My App" --app-exec myapp \
    --mac-notarize \
    --mac-sign-identity "Developer ID Application: Example, Inc. (TEAMID1234)" \
    --mac-notary-keychain-profile easyinstaller-notary
```