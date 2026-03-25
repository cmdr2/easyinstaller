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

Run: `easyinstaller --source ./build --os linux --arch x86_64 --type appimage --output myapp --app-name "My App" --app-version 1.0.0 --app-exec myapp`.

`myapp.AppImage` will be written in the current directory.

## flatpak

1. Install Flatpak tooling. On Debian or Ubuntu: `sudo apt-get update && sudo apt-get install -y flatpak flatpak-builder`. On Fedora: `sudo dnf install -y flatpak flatpak-builder`.
2. Run: `easyinstaller --source ./build --os linux --arch x86_64 --type flatpak --output myapp --app-name "My App" --app-version 1.0.0 --app-exec myapp`.

`myapp.flatpak` will be written in the current directory.

## snap

1. Install Snapcraft with `sudo snap install snapcraft --classic`, or follow https://snapcraft.io/docs/installing-snapcraft.
2. Run: `easyinstaller --source ./build --os linux --arch x86_64 --type snap --output myapp --app-name "My App" --app-version 1.0.0 --app-exec myapp`.

`myapp.snap` will be written in the current directory.
