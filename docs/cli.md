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
| `--app-name` | basename of `--output` | deb, rpm, nsis, appimage, flatpak, snap, dmg, app, app-in-dmg, pkg, app-in-pkg |
| `--app-version` | `1.0.0` | all installer types |
| `--app-description` | `Application packaged with easyinstaller` | deb, rpm, snap |
| `--app-maintainer` | `maintainer@example.com` | deb |
| `--app-category` | `Utility` | deb, appimage |
| `--app-exec` | none | nsis, appimage, flatpak, snap, pkg, app, app-in-dmg, app-in-pkg. Optional for nsis and pkg; required for the other listed targets and must stay inside the source tree |
| `--app-icon` | none | appimage, app |

## mac notarization flags

| Flag | Default | Notes |
|------|---------|-------|
| `--mac-notarize` | off | Enables signing and notarization for mac targets |
| `--mac-notary-team-name` | none | Required with `--mac-notarize`; used to derive `Developer ID Application` and `Developer ID Installer` signing identities |
| `--mac-notary-keychain-profile` | none | Name of a `notarytool` keychain profile created with `xcrun notarytool store-credentials` |
| `--mac-notary-apple-id` | none | Use with direct credentials if no keychain profile is configured |
| `--mac-notary-team-id` | none | Use with direct credentials if no keychain profile is configured |
| `--mac-notary-password` | none | Use with direct credentials if no keychain profile is configured |

When notarization is enabled, easyinstaller derives `Developer ID Application: <team name> (<team id>)` for payload signing and `Developer ID Installer: <team name> (<team id>)` for `pkg` outputs. It copies the source into a staging folder, signs copied binaries there, submits the final output with `xcrun notarytool submit --wait`, and staples the result when Apple supports stapling for that format.

## Notes

| Topic | Detail |
|-------|--------|
| Supported Windows types | `zip`, `tar.gz`, `nsis` |
| Supported Linux types | `zip`, `tar.gz`, `deb`, `rpm`, `appimage`, `flatpak`, `snap` |
| Supported Mac types | `zip`, `tar.gz`, `dmg`, `app`, `app-in-dmg`, `pkg`, `app-in-pkg` |
| Accepted arch names | `x86_64`, `arm64`, `i386`, `armhf` |
| Output folders | `--output dist/release/` creates `dist/release/release.<ext>` |
| Plain `pkg` default layout | Installs payload under `/opt/<sanitised-app-name>` and, when `--app-exec` is set, adds a launcher at `/usr/local/bin/<basename(app-exec)>` |
| Stapled mac targets | `app`, `dmg`, `app-in-dmg`, `pkg`, `app-in-pkg` |
| Submitted but not stapled | `zip` |

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
    --mac-notary-team-name "Example, Inc." \
    --mac-notary-team-id TEAMID1234 \
    --mac-notary-keychain-profile easyinstaller-notary

# notarized macOS app-in-pkg
easyinstaller --source ./build --os mac --arch arm64 --type app-in-pkg \
    --output MyApp \
    --app-name "My App" --app-version 1.0.0 --app-exec myapp \
    --mac-notarize \
    --mac-notary-team-name "Example, Inc." \
    --mac-notary-team-id TEAMID1234 \
    --mac-notary-keychain-profile easyinstaller-notary
```