# Linux guide

Use a Linux machine for Linux targets, especially when native tools are involved.

## zip

Run: `easyinstaller --source ./build --os linux --arch x86_64 --type zip --output myapp-linux-x64`.

`myapp-linux-x64.zip` will be written in the current directory.

## tar.gz

Run: `easyinstaller --source ./build --os linux --arch x86_64 --type tar.gz --output myapp-linux-x64`.

`myapp-linux-x64.tar.gz` will be written in the current directory.

## deb

1. Install `dpkg-deb`. On Debian or Ubuntu: `sudo apt-get update && sudo apt-get install -y dpkg`.
2. Run: `easyinstaller --source ./build --os linux --arch x86_64 --type deb --output myapp --app-name "My App" --app-version 1.0.0 --app-exec myapp`.

`myapp.deb` will be written in the current directory.

## rpm

1. Install `rpmbuild`. On Fedora: `sudo dnf install -y rpm-build`. On Debian or Ubuntu: `sudo apt-get install -y rpm`.
2. Run: `easyinstaller --source ./build --os linux --arch x86_64 --type rpm --output myapp --app-name "My App" --app-version 1.0.0 --app-exec myapp`.

`myapp.rpm` will be written in the current directory.

## appimage

1. Install `appimagetool` and ensure it is available on `PATH`. You can download the release artifact from https://github.com/AppImage/appimagetool/releases and make it executable.
2. Run: `easyinstaller --source ./build --os linux --arch x86_64 --type appimage --output myapp --app-name "My App" --app-version 1.0.0 --app-exec myapp`.

`myapp.AppImage` will be written in the current directory.

## flatpak

1. Install Flatpak tooling:
- On Debian or Ubuntu: `sudo apt-get update && sudo apt-get install -y flatpak flatpak-builder`
- On Fedora: `sudo dnf install -y flatpak flatpak-builder`
- `easyinstaller` currently targets the Freedesktop `24.08` runtime and SDK when building Flatpaks.
2. Run: `easyinstaller --source ./build --os linux --arch x86_64 --type flatpak --output myapp --app-name "My App" --app-version 1.0.0 --app-exec myapp`.

`myapp.flatpak` will be written in the current directory.

## snap

1. Install the snap tooling. On Debian or Ubuntu: `sudo apt-get update && sudo apt-get install -y snapd squashfs-tools`.
2. Ensure the `snap` command is available on `PATH`.
3. Run: `easyinstaller --source ./build --os linux --arch x86_64 --type snap --output myapp --app-name "My App" --app-version 1.0.0 --app-exec myapp`.

`myapp.snap` will be written in the current directory.
