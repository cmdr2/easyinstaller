#!/usr/bin/env bash
#
# easy-installer.sh - Create installers and archives from a release folder.
#
# Usage:
#   ./easy-installer.sh --source <dir> --os <os> --arch <arch> --type <type> --output <name> [options]
#
# See --help for full usage information.
#

set -euo pipefail

##############################################################################
# Defaults and constants
##############################################################################
VERSION="1.0.0"

SOURCE_DIR=""
TARGET_OS=""
TARGET_ARCH=""
TARGET_TYPE=""
OUTPUT_NAME=""

# Optional metadata (used by some installer formats)
APP_NAME=""
APP_VERSION="1.0.0"
APP_DESCRIPTION="Application packaged with easy-installer"
APP_MAINTAINER="maintainer@example.com"
APP_CATEGORY="Utility"
APP_EXEC=""
APP_ICON=""

##############################################################################
# Helpers
##############################################################################
log()   { echo "[easy-installer] $*"; }
warn()  { echo "[easy-installer] WARNING: $*" >&2; }
error() { echo "[easy-installer] ERROR: $*" >&2; exit 1; }

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || error "'$1' is required but not found. Please install it."
}

usage() {
    cat <<EOF
easy-installer v${VERSION}

Create an installer or archive from a release folder.

USAGE:
    $0 [OPTIONS]

REQUIRED OPTIONS:
    --source <dir>        Path to the release folder to package
    --os <os>             Target operating system: windows, linux, mac
    --arch <arch>         Target architecture: x86_64, arm64, i386, armhf
    --type <type>         Package type (see below)
    --output <name>       Output file name (without extension)

OPTIONAL:
    --app-name <name>     Application name (defaults to output name)
    --app-version <ver>   Application version (default: 1.0.0)
    --app-description <d> Short description of the application
    --app-maintainer <m>  Maintainer email (default: maintainer@example.com)
    --app-category <c>    Application category (default: Utility)
    --app-exec <exe>      Main executable name (relative to source dir)
    --app-icon <icon>     Path to application icon (PNG for Linux, ICNS for Mac)
    --help                Show this help message
    --version             Show version

SUPPORTED TYPES:
    Windows:  zip, tar.gz, nsis
    Linux:    zip, tar.gz, deb, rpm, appimage, flatpak, snap
    Mac:      zip, tar.gz, dmg, app

EXAMPLES:
    # Create a .tar.gz archive for Linux x86_64
    $0 --source ./build --os linux --arch x86_64 --type tar.gz --output myapp-1.0.0-linux-x64

    # Create a .deb package
    $0 --source ./build --os linux --arch x86_64 --type deb --output myapp \\
       --app-name "My App" --app-version 1.0.0 --app-exec myapp

    # Create a Windows NSIS installer
    $0 --source ./build --os windows --arch x86_64 --type nsis --output myapp-setup \\
       --app-name "My App" --app-version 1.0.0

    # Create a macOS .dmg
    $0 --source ./build --os mac --arch arm64 --type dmg --output myapp-1.0.0
EOF
}

##############################################################################
# Argument parsing
##############################################################################
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --source)         SOURCE_DIR="$2"; shift 2 ;;
            --os)             TARGET_OS="$2"; shift 2 ;;
            --arch)           TARGET_ARCH="$2"; shift 2 ;;
            --type)           TARGET_TYPE="$2"; shift 2 ;;
            --output)         OUTPUT_NAME="$2"; shift 2 ;;
            --app-name)       APP_NAME="$2"; shift 2 ;;
            --app-version)    APP_VERSION="$2"; shift 2 ;;
            --app-description) APP_DESCRIPTION="$2"; shift 2 ;;
            --app-maintainer) APP_MAINTAINER="$2"; shift 2 ;;
            --app-category)   APP_CATEGORY="$2"; shift 2 ;;
            --app-exec)       APP_EXEC="$2"; shift 2 ;;
            --app-icon)       APP_ICON="$2"; shift 2 ;;
            --help)           usage; exit 0 ;;
            --version)        echo "easy-installer v${VERSION}"; exit 0 ;;
            *)                error "Unknown option: $1. Use --help for usage." ;;
        esac
    done
}

validate_args() {
    [[ -z "$SOURCE_DIR" ]]  && error "--source is required"
    [[ -z "$TARGET_OS" ]]   && error "--os is required"
    [[ -z "$TARGET_ARCH" ]] && error "--arch is required"
    [[ -z "$TARGET_TYPE" ]] && error "--type is required"
    [[ -z "$OUTPUT_NAME" ]] && error "--output is required"

    # Resolve to absolute path
    SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)" || error "Source directory does not exist: $SOURCE_DIR"
    [[ -d "$SOURCE_DIR" ]] || error "Source directory does not exist: $SOURCE_DIR"

    # Normalize OS
    case "$TARGET_OS" in
        windows|win)   TARGET_OS="windows" ;;
        linux)         TARGET_OS="linux" ;;
        mac|macos|osx) TARGET_OS="mac" ;;
        *)             error "Unsupported OS: $TARGET_OS. Use: windows, linux, mac" ;;
    esac

    # Normalize arch
    case "$TARGET_ARCH" in
        x86_64|amd64|x64) TARGET_ARCH="x86_64" ;;
        arm64|aarch64)     TARGET_ARCH="arm64" ;;
        i386|i686|x86)     TARGET_ARCH="i386" ;;
        armhf|armv7l)      TARGET_ARCH="armhf" ;;
        *)                 error "Unsupported arch: $TARGET_ARCH. Use: x86_64, arm64, i386, armhf" ;;
    esac

    # Normalize type
    case "$TARGET_TYPE" in
        zip)       TARGET_TYPE="zip" ;;
        tar.gz|targz|tgz) TARGET_TYPE="tar.gz" ;;
        nsis)      TARGET_TYPE="nsis" ;;
        deb)       TARGET_TYPE="deb" ;;
        rpm)       TARGET_TYPE="rpm" ;;
        appimage)  TARGET_TYPE="appimage" ;;
        flatpak)   TARGET_TYPE="flatpak" ;;
        snap)      TARGET_TYPE="snap" ;;
        dmg)       TARGET_TYPE="dmg" ;;
        app)       TARGET_TYPE="app" ;;
        *)         error "Unsupported type: $TARGET_TYPE. Use: zip, tar.gz, nsis, deb, rpm, appimage, flatpak, snap, dmg, app" ;;
    esac

    # Validate OS + type combinations
    case "$TARGET_OS" in
        windows)
            case "$TARGET_TYPE" in
                zip|tar.gz|nsis) ;;
                *) error "Type '$TARGET_TYPE' is not supported for Windows. Use: zip, tar.gz, nsis" ;;
            esac
            ;;
        linux)
            case "$TARGET_TYPE" in
                zip|tar.gz|deb|rpm|appimage|flatpak|snap) ;;
                *) error "Type '$TARGET_TYPE' is not supported for Linux. Use: zip, tar.gz, deb, rpm, appimage, flatpak, snap" ;;
            esac
            ;;
        mac)
            case "$TARGET_TYPE" in
                zip|tar.gz|dmg|app) ;;
                *) error "Type '$TARGET_TYPE' is not supported for Mac. Use: zip, tar.gz, dmg, app" ;;
            esac
            ;;
    esac

    # Resolve OUTPUT_NAME to an absolute path
    case "$OUTPUT_NAME" in
        /*) ;; # already absolute
        *)  OUTPUT_NAME="$(pwd)/$OUTPUT_NAME" ;;
    esac

    # Default app name to output base name
    if [[ -z "$APP_NAME" ]]; then
        APP_NAME="$(basename "$OUTPUT_NAME")"
    fi
}

##############################################################################
# Arch mapping helpers
##############################################################################
deb_arch() {
    case "$TARGET_ARCH" in
        x86_64) echo "amd64" ;;
        arm64)  echo "arm64" ;;
        i386)   echo "i386" ;;
        armhf)  echo "armhf" ;;
    esac
}

rpm_arch() {
    case "$TARGET_ARCH" in
        x86_64) echo "x86_64" ;;
        arm64)  echo "aarch64" ;;
        i386)   echo "i686" ;;
        armhf)  echo "armv7hl" ;;
    esac
}

##############################################################################
# Package builders
##############################################################################

build_zip() {
    require_cmd zip
    local output_file="${OUTPUT_NAME}.zip"
    log "Creating zip archive: $output_file"
    (cd "$(dirname "$SOURCE_DIR")" && zip -r "$output_file" "$(basename "$SOURCE_DIR")")
    log "Created: $output_file"
}

build_tar_gz() {
    require_cmd tar
    local output_file="${OUTPUT_NAME}.tar.gz"
    log "Creating tar.gz archive: $output_file"
    tar -czf "$output_file" -C "$(dirname "$SOURCE_DIR")" "$(basename "$SOURCE_DIR")"
    log "Created: $output_file"
}

build_nsis() {
    require_cmd makensis
    local output_file="${OUTPUT_NAME}.exe"
    local nsis_script
    nsis_script="$(mktemp /tmp/easy-installer-nsis-XXXXXX.nsi)"

    log "Creating NSIS installer: $output_file"

    # Generate the list of files to install and uninstall
    local install_files=""
    local uninstall_files=""
    local install_dirs=""
    local uninstall_dirs=""

    while IFS= read -r -d '' file; do
        local rel="${file#"$SOURCE_DIR"/}"
        local dir
        dir="$(dirname "$rel")"
        if [[ "$dir" != "." ]]; then
            install_dirs+="  CreateDirectory \"\$INSTDIR\\${dir//\//\\}\""$'\n'
            uninstall_dirs+="  RMDir \"\$INSTDIR\\${dir//\//\\}\""$'\n'
        fi
        install_files+="  SetOutPath \"\$INSTDIR\\${dir//\//\\}\""$'\n'
        install_files+="  File \"${file//\//\\}\""$'\n'
        uninstall_files+="  Delete \"\$INSTDIR\\${rel//\//\\}\""$'\n'
    done < <(find "$SOURCE_DIR" -type f -print0 | sort -z)

    cat > "$nsis_script" <<NSIS_EOF
!include "MUI2.nsh"

Name "${APP_NAME}"
OutFile "$(pwd)/${output_file}"
InstallDir "\$PROGRAMFILES\\${APP_NAME}"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
${install_files}
  ; Create uninstaller
  WriteUninstaller "\$INSTDIR\\Uninstall.exe"

  ; Start menu shortcut
  CreateDirectory "\$SMPROGRAMS\\${APP_NAME}"
  CreateShortcut "\$SMPROGRAMS\\${APP_NAME}\\Uninstall.lnk" "\$INSTDIR\\Uninstall.exe"

  ; Add/Remove Programs entry
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "\$INSTDIR\\Uninstall.exe"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
SectionEnd

Section "Uninstall"
${uninstall_files}
  Delete "\$INSTDIR\\Uninstall.exe"
${uninstall_dirs}
  RMDir "\$INSTDIR"

  ; Remove Start menu items
  Delete "\$SMPROGRAMS\\${APP_NAME}\\Uninstall.lnk"
  RMDir "\$SMPROGRAMS\\${APP_NAME}"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
SectionEnd
NSIS_EOF

    makensis "$nsis_script"
    rm -f "$nsis_script"
    log "Created: $output_file"
}

build_deb() {
    require_cmd dpkg-deb
    local output_file="${OUTPUT_NAME}.deb"
    local deb_root
    deb_root="$(mktemp -d /tmp/easy-installer-deb-XXXXXX)"
    local install_prefix="opt/${APP_NAME}"

    log "Creating deb package: $output_file"

    mkdir -p "${deb_root}/${install_prefix}"
    cp -a "$SOURCE_DIR"/. "${deb_root}/${install_prefix}/"
    mkdir -p "${deb_root}/DEBIAN"

    cat > "${deb_root}/DEBIAN/control" <<EOF
Package: $(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | tr '[:space:]' '-' | sed 's/--*/-/g; s/^-//; s/-$//')
Version: ${APP_VERSION}
Architecture: $(deb_arch)
Maintainer: ${APP_MAINTAINER}
Description: ${APP_DESCRIPTION}
Section: ${APP_CATEGORY}
Priority: optional
EOF

    # If an executable is specified, create a symlink in /usr/bin
    if [[ -n "$APP_EXEC" ]]; then
        mkdir -p "${deb_root}/usr/bin"
        ln -s "/${install_prefix}/${APP_EXEC}" "${deb_root}/usr/bin/${APP_EXEC}"
    fi

    dpkg-deb --build --root-owner-group "$deb_root" "$output_file"
    rm -rf "$deb_root"
    log "Created: $output_file"
}

build_rpm() {
    require_cmd rpmbuild
    local output_file="${OUTPUT_NAME}.rpm"
    local rpm_root
    rpm_root="$(mktemp -d /tmp/easy-installer-rpm-XXXXXX)"
    local install_prefix="opt/${APP_NAME}"
    local sanitized_name
    sanitized_name="$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | tr '[:space:]' '-' | sed 's/--*/-/g; s/^-//; s/-$//')"

    log "Creating rpm package: $output_file"

    mkdir -p "${rpm_root}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS,BUILDROOT}

    # Create tarball source
    local src_staging
    src_staging="$(mktemp -d /tmp/easy-installer-rpmsrc-XXXXXX)"
    mkdir -p "${src_staging}/${sanitized_name}-${APP_VERSION}"
    cp -a "$SOURCE_DIR"/. "${src_staging}/${sanitized_name}-${APP_VERSION}/"
    tar -czf "${rpm_root}/SOURCES/${sanitized_name}-${APP_VERSION}.tar.gz" \
        -C "$src_staging" "${sanitized_name}-${APP_VERSION}"
    rm -rf "$src_staging"

    # Generate file list from source dir
    local file_list=""
    while IFS= read -r -d '' file; do
        local rel="${file#"$SOURCE_DIR"}"
        file_list+="\"/${install_prefix}${rel}\""$'\n'
    done < <(find "$SOURCE_DIR" -type f -print0 | sort -z)

    cat > "${rpm_root}/SPECS/${sanitized_name}.spec" <<SPEC_EOF
Name:           ${sanitized_name}
Version:        ${APP_VERSION}
Release:        1
Summary:        ${APP_DESCRIPTION}
License:        Proprietary
Source0:        ${sanitized_name}-${APP_VERSION}.tar.gz

%description
${APP_DESCRIPTION}

%prep
%setup -q -n ${sanitized_name}-${APP_VERSION}

%install
mkdir -p %{buildroot}/${install_prefix}
cp -a . %{buildroot}/${install_prefix}/

%files
/${install_prefix}
SPEC_EOF

    rpmbuild --define "_topdir ${rpm_root}" \
             --target "$(rpm_arch)" \
             -bb "${rpm_root}/SPECS/${sanitized_name}.spec"

    # Find and move the built RPM
    local built_rpm
    built_rpm="$(find "${rpm_root}/RPMS" -name '*.rpm' -type f | head -1)"
    [[ -f "$built_rpm" ]] || error "RPM build failed - no output found"
    cp "$built_rpm" "$output_file"
    rm -rf "$rpm_root"
    log "Created: $output_file"
}

build_appimage() {
    local output_file="${OUTPUT_NAME}.AppImage"
    local appdir
    appdir="$(mktemp -d /tmp/easy-installer-appimage-XXXXXX)"

    log "Creating AppImage: $output_file"

    [[ -n "$APP_EXEC" ]] || error "--app-exec is required for AppImage"

    # Set up AppDir structure
    mkdir -p "${appdir}/usr/bin"
    mkdir -p "${appdir}/usr/share/applications"
    mkdir -p "${appdir}/usr/share/icons/hicolor/256x256/apps"
    cp -a "$SOURCE_DIR"/. "${appdir}/usr/bin/"

    # Create .desktop file
    cat > "${appdir}/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Exec=${APP_EXEC}
Icon=${APP_NAME}
Categories=${APP_CATEGORY};
EOF
    cp "${appdir}/${APP_NAME}.desktop" "${appdir}/usr/share/applications/${APP_NAME}.desktop"

    # Icon
    if [[ -n "$APP_ICON" && -f "$APP_ICON" ]]; then
        cp "$APP_ICON" "${appdir}/${APP_NAME}.png"
        cp "$APP_ICON" "${appdir}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
    else
        # Create a minimal 1x1 PNG placeholder so appimagetool doesn't fail
        if command -v convert >/dev/null 2>&1; then
            convert -size 256x256 xc:transparent "${appdir}/${APP_NAME}.png"
        else
            # Minimal valid 1x1 PNG (base64 encoded)
            echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > "${appdir}/${APP_NAME}.png"
        fi
        cp "${appdir}/${APP_NAME}.png" "${appdir}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
    fi

    # Create AppRun
    cat > "${appdir}/AppRun" <<'APPRUN_EOF'
#!/bin/bash
SELF="$(readlink -f "$0")"
HERE="$(dirname "$SELF")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
APPRUN_EOF
    echo "exec \"\${HERE}/usr/bin/${APP_EXEC}\" \"\$@\"" >> "${appdir}/AppRun"
    chmod +x "${appdir}/AppRun"

    # Download appimagetool if not available
    local appimagetool=""
    if command -v appimagetool >/dev/null 2>&1; then
        appimagetool="appimagetool"
    elif [[ -x "/tmp/appimagetool" ]]; then
        appimagetool="/tmp/appimagetool"
    else
        log "Downloading appimagetool..."
        local arch_suffix="x86_64"
        [[ "$TARGET_ARCH" == "arm64" ]] && arch_suffix="aarch64"
        curl -fSL "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${arch_suffix}.AppImage" \
            -o /tmp/appimagetool || error "Failed to download appimagetool"
        chmod +x /tmp/appimagetool
        appimagetool="/tmp/appimagetool"
    fi

    ARCH="$TARGET_ARCH" "$appimagetool" "$appdir" "$output_file" || \
        ARCH="$TARGET_ARCH" "$appimagetool" --appimage-extract-and-run "$appdir" "$output_file"
    rm -rf "$appdir"
    log "Created: $output_file"
}

build_flatpak() {
    require_cmd flatpak
    require_cmd flatpak-builder
    local output_file="${OUTPUT_NAME}.flatpak"
    local build_dir
    build_dir="$(mktemp -d /tmp/easy-installer-flatpak-XXXXXX)"
    local sanitized_id
    sanitized_id="com.$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g').app"

    log "Creating Flatpak: $output_file"

    [[ -n "$APP_EXEC" ]] || error "--app-exec is required for Flatpak"

    # Ensure the freedesktop runtime is available
    flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
    flatpak install --user -y flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08 2>/dev/null || true

    mkdir -p "${build_dir}/source"
    cp -a "$SOURCE_DIR"/. "${build_dir}/source/"

    # Create manifest
    cat > "${build_dir}/manifest.json" <<EOF
{
    "app-id": "${sanitized_id}",
    "runtime": "org.freedesktop.Platform",
    "runtime-version": "23.08",
    "sdk": "org.freedesktop.Sdk",
    "command": "${APP_EXEC}",
    "modules": [
        {
            "name": "${APP_NAME}",
            "buildsystem": "simple",
            "build-commands": [
                "mkdir -p /app/bin",
                "cp -a . /app/bin/"
            ],
            "sources": [
                {
                    "type": "dir",
                    "path": "source"
                }
            ]
        }
    ]
}
EOF

    flatpak-builder --user --force-clean "${build_dir}/build" "${build_dir}/manifest.json"
    flatpak build-export "${build_dir}/repo" "${build_dir}/build"
    flatpak build-bundle "${build_dir}/repo" "$output_file" "$sanitized_id"
    rm -rf "$build_dir"
    log "Created: $output_file"
}

build_snap() {
    require_cmd snapcraft
    local output_file="${OUTPUT_NAME}.snap"
    local snap_dir
    snap_dir="$(mktemp -d /tmp/easy-installer-snap-XXXXXX)"
    local sanitized_name
    sanitized_name="$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | tr '[:space:]' '-' | sed 's/--*/-/g; s/^-//; s/-$//')"

    log "Creating Snap: $output_file"

    [[ -n "$APP_EXEC" ]] || error "--app-exec is required for Snap"

    mkdir -p "${snap_dir}/snap"
    cp -a "$SOURCE_DIR"/. "${snap_dir}/source/"

    cat > "${snap_dir}/snap/snapcraft.yaml" <<EOF
name: ${sanitized_name}
version: '${APP_VERSION}'
summary: ${APP_DESCRIPTION}
description: |
  ${APP_DESCRIPTION}
base: core22
grade: stable
confinement: strict

parts:
  ${sanitized_name}:
    plugin: dump
    source: ../source/

apps:
  ${sanitized_name}:
    command: ${APP_EXEC}
EOF

    (cd "$snap_dir" && snapcraft --destructive-mode)
    local built_snap
    built_snap="$(find "$snap_dir" -name '*.snap' -type f | head -1)"
    [[ -f "$built_snap" ]] || error "Snap build failed - no output found"
    cp "$built_snap" "$output_file"
    rm -rf "$snap_dir"
    log "Created: $output_file"
}

build_dmg() {
    require_cmd hdiutil
    local output_file="${OUTPUT_NAME}.dmg"
    local dmg_staging
    dmg_staging="$(mktemp -d /tmp/easy-installer-dmg-XXXXXX)"

    log "Creating DMG: $output_file"

    cp -a "$SOURCE_DIR"/. "${dmg_staging}/"

    hdiutil create -volname "$APP_NAME" \
        -srcfolder "$dmg_staging" \
        -ov -format UDZO \
        "$output_file"

    rm -rf "$dmg_staging"
    log "Created: $output_file"
}

build_app() {
    local output_file="${OUTPUT_NAME}.app"

    log "Creating .app bundle: $output_file"

    [[ -n "$APP_EXEC" ]] || error "--app-exec is required for .app bundles"

    mkdir -p "${output_file}/Contents/MacOS"
    mkdir -p "${output_file}/Contents/Resources"

    cp -a "$SOURCE_DIR"/. "${output_file}/Contents/Resources/"

    # Create launch script in MacOS/
    cat > "${output_file}/Contents/MacOS/${APP_EXEC}" <<LAUNCH_EOF
#!/bin/bash
DIR="\$(cd "\$(dirname "\$0")/../Resources" && pwd)"
exec "\${DIR}/${APP_EXEC}" "\$@"
LAUNCH_EOF
    chmod +x "${output_file}/Contents/MacOS/${APP_EXEC}"

    # Create Info.plist
    local bundle_id
    bundle_id="com.$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g').app"
    cat > "${output_file}/Contents/Info.plist" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_EXEC}</string>
    <key>CFBundleIdentifier</key>
    <string>${bundle_id}</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>${APP_VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${APP_VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
PLIST_EOF

    # Copy icon if provided
    if [[ -n "$APP_ICON" && -f "$APP_ICON" ]]; then
        cp "$APP_ICON" "${output_file}/Contents/Resources/$(basename "$APP_ICON")"
    fi

    log "Created: $output_file"
}

##############################################################################
# Main
##############################################################################
main() {
    parse_args "$@"
    validate_args

    log "Packaging: source=$SOURCE_DIR os=$TARGET_OS arch=$TARGET_ARCH type=$TARGET_TYPE output=$OUTPUT_NAME"

    case "$TARGET_TYPE" in
        zip)       build_zip ;;
        tar.gz)    build_tar_gz ;;
        nsis)      build_nsis ;;
        deb)       build_deb ;;
        rpm)       build_rpm ;;
        appimage)  build_appimage ;;
        flatpak)   build_flatpak ;;
        snap)      build_snap ;;
        dmg)       build_dmg ;;
        app)       build_app ;;
        *)         error "Unhandled type: $TARGET_TYPE" ;;
    esac
}

# Only run main when executed directly (not when sourced for testing)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
