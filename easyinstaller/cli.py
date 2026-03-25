"""Command-line interface for easyinstaller."""

from __future__ import annotations

import argparse
import logging
import sys

from .config import (
    TYPES_BY_OS,
    Config,
    ConfigError,
    validate_and_normalise,
)
from .builders import build

log = logging.getLogger("easyinstaller")


def _build_parser() -> argparse.ArgumentParser:
    all_types = sorted({t for types in TYPES_BY_OS.values() for t in types})
    parser = argparse.ArgumentParser(
        prog="easyinstaller",
        description="Create an installer or archive from a release folder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "supported types:\n"
            "  Windows:  zip, tar.gz, nsis\n"
            "  Linux:    zip, tar.gz, deb, rpm, appimage, flatpak, snap\n"
            "  Mac:      zip, tar.gz, dmg, app, app-in-dmg\n"
            "\n"
            "examples:\n"
            "  easyinstaller --source ./build --os linux --arch x86_64 --type tar.gz --output myapp-linux-x64\n"
            "  easyinstaller --source ./build --os linux --arch x86_64 --type deb --output myapp \\\n"
            "      --app-name MyApp --app-version 1.0.0 --app-exec myapp\n"
            "  easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg --output MyApp \\\n"
            '      --app-name MyApp --app-exec myapp --mac-notarize --mac-sign-identity "Developer ID Application: Example" \\\n'
            "      --mac-notary-keychain-profile my-notary-profile\n"
        ),
    )

    required = parser.add_argument_group("required arguments")
    required.add_argument("--source", required=True, help="Path to the release folder to package")
    required.add_argument("--os", required=True, dest="target_os", help="Target OS: windows, linux, mac")
    required.add_argument(
        "--arch",
        required=True,
        help="Target architecture: x86_64, arm64, i386, armhf",
    )
    required.add_argument("--type", required=True, dest="target_type", help=f"Package type: {', '.join(all_types)}")
    required.add_argument(
        "--output",
        required=True,
        help="Output file name without extension, or a folder path whose last segment will be used as the file name",
    )

    optional = parser.add_argument_group("optional metadata")
    optional.add_argument("--app-name", default="", help="Application name (defaults to output name)")
    optional.add_argument("--app-version", default="1.0.0", help="Application version (default: 1.0.0)")
    optional.add_argument(
        "--app-description", default="Application packaged with easyinstaller", help="Short description"
    )
    optional.add_argument("--app-maintainer", default="maintainer@example.com", help="Maintainer email")
    optional.add_argument("--app-category", default="Utility", help="Application category")
    optional.add_argument(
        "--app-exec",
        default=None,
        help="Main executable path relative to the source dir; enables the finish-page launch option for NSIS",
    )
    optional.add_argument("--app-icon", default=None, help="Path to application icon")

    mac = parser.add_argument_group("mac notarization")
    mac.add_argument("--mac-notarize", action="store_true", help="Sign and submit mac outputs for notarization")
    mac.add_argument(
        "--mac-sign-identity",
        default=None,
        help="codesign identity, for example a Developer ID Application certificate",
    )
    mac.add_argument(
        "--mac-notary-keychain-profile",
        default=None,
        help="notarytool keychain profile to use for authentication",
    )
    mac.add_argument("--mac-notary-apple-id", default=None, help="Apple ID email for notarytool authentication")
    mac.add_argument("--mac-notary-team-id", default=None, help="Apple developer team ID for notarytool authentication")
    mac.add_argument("--mac-notary-password", default=None, help="App-specific password for notarytool authentication")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[easyinstaller] %(message)s",
    )

    cfg = Config(
        source=args.source,
        target_os=args.target_os,
        arch=args.arch,
        target_type=args.target_type,
        output=args.output,
        app_name=args.app_name,
        app_version=args.app_version,
        app_description=args.app_description,
        app_maintainer=args.app_maintainer,
        app_category=args.app_category,
        app_exec=args.app_exec,
        app_icon=args.app_icon,
        mac_notarize=args.mac_notarize,
        mac_sign_identity=args.mac_sign_identity,
        mac_notary_keychain_profile=args.mac_notary_keychain_profile,
        mac_notary_apple_id=args.mac_notary_apple_id,
        mac_notary_team_id=args.mac_notary_team_id,
        mac_notary_password=args.mac_notary_password,
    )

    try:
        cfg = validate_and_normalise(cfg)
    except ConfigError as exc:
        log.error("%s", exc)
        return 1

    log.info(
        "Packaging: source=%s os=%s arch=%s type=%s output=%s",
        cfg.source,
        cfg.target_os,
        cfg.arch,
        cfg.target_type,
        cfg.output,
    )

    try:
        result = build(cfg)
        log.info("Done: %s", result)
    except Exception as exc:
        log.error("Build failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
