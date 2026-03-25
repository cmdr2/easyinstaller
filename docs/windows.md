# Windows guide

Use a Windows machine for Windows targets.

## zip

Run: `easyinstaller --source .\build --os windows --arch x86_64 --type zip --output myapp-windows-x64`.

`myapp-windows-x64.zip` will be written in the current directory.

## tar.gz

Run: `easyinstaller --source .\build --os windows --arch x86_64 --type tar.gz --output myapp-windows-x64`.

`myapp-windows-x64.tar.gz` will be written in the current directory.

## nsis

1. Install [NSIS](https://sourceforge.net/projects/nsis/files/NSIS%203/3.11/nsis-3.11.zip/download).
2. Confirm `makensis.exe` is on `PATH`.
3. Run: `easyinstaller --source .\build --os windows --arch x86_64 --type nsis --output myapp-setup --app-name "My App" --app-version 1.0.0 --app-exec bin\myapp.exe`.

If `--app-exec` is set, the installer finish page shows a checkbox to start that executable after setup completes.

`myapp-setup.exe` will be written in the current directory.
