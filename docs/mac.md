# macOS guide

Use a macOS machine for mac targets.

## zip

Run: `easyinstaller --source ./build --os mac --arch arm64 --type zip --output MyApp-mac-arm64`.

`MyApp-mac-arm64.zip` will be written in the current directory.

## tar.gz

Run: `easyinstaller --source ./build --os mac --arch arm64 --type tar.gz --output MyApp-mac-arm64`.

`MyApp-mac-arm64.tar.gz` will be written in the current directory.

`tar.gz` outputs can contain signed binaries, but Apple notarization submission is not supported for this type because `notarytool submit` accepts `.zip`, `.pkg`, and `.dmg`, not `.tar.gz`.

## dmg

Run: `easyinstaller --source ./build --os mac --arch arm64 --type dmg --output MyApp --app-name "My App"`.

`MyApp.dmg` will be written in the current directory.

## app

Run: `easyinstaller --source ./build --os mac --arch arm64 --type app --output MyApp --app-name "My App" --app-exec myapp`.

`MyApp.app` will be written in the current directory.

## app-in-dmg

Run: `easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg --output MyApp --app-name "My App" --app-exec myapp`.

`MyApp.dmg` will be written in the current directory.

## pkg

Run: `easyinstaller --source ./build --os mac --arch arm64 --type pkg --output MyApp --app-name "My App"`.

`MyApp.pkg` will be written in the current directory.

For a plain `pkg`, easyinstaller uses system-tool style packaging rather than app-bundle style packaging.

- The payload is installed under `/opt/my-app` where `my-app` is a sanitised form of `--app-name`.
- If you pass `--app-exec`, easyinstaller also installs a small launcher script at `/usr/local/bin/<basename(app-exec)>` that runs the packaged executable from `/opt/my-app/...`.
- The generated product archive enables user-home installation in macOS Installer, so a non-admin install can target `~/opt/my-app` and `~/usr/local/bin/<executable>`.
- If you install with `installer -target CurrentUserHomeDirectory`, those become `~/opt/my-app` and `~/usr/local/bin/<executable>`.

This keeps plain `pkg` useful for CLI and non-bundle tools. If you want Finder-first UX, use `app`, `app-in-dmg`, or `app-in-pkg` instead.

## app-in-pkg

Run: `easyinstaller --source ./build --os mac --arch arm64 --type app-in-pkg --output MyApp --app-name "My App" --app-version 1.0.0 --app-exec myapp`.

`MyApp.pkg` will be written in the current directory.

The installed app bundle goes under `Applications/My App.app` on the target volume, or `~/Applications/My App.app` when installed into the user home domain. The generated product archive enables that per-user install path so it can be installed without admin permissions.

## Notarization

*You can skip the 'Common setup' section if you already have valid Developer ID certificates and an app-specific password.*

`--mac-notarize` is supported for mac types `zip`, `dmg`, `app`, `app-in-dmg`, `pkg`, and `app-in-pkg`. It is not supported for `tar.gz`.

easyinstaller derives the signing identity from `--mac-notary-team-name` and `--mac-notary-team-id`.

- `zip`, `dmg`, `app`, and `app-in-dmg` use `Developer ID Application: <team name> (<team id>)`.
- `pkg` and `app-in-pkg` sign payload binaries with `Developer ID Application: <team name> (<team id>)`, then sign the installer itself with `Developer ID Installer: <team name> (<team id>)`.

### Common setup

1. Join the Apple Developer Program: https://developer.apple.com/programs/.
2. Open Certificates, IDs & Profiles: https://developer.apple.com/account/resources/certificates/list.
3. Generate a private key and CSR on any machine:
- `openssl genrsa -out developer-id.key 2048`
- `openssl req -new -key developer-id.key -out developer-id.csr -subj "/CN=DOES_NOT_MATTER/OU=DOES_NOT_MATTER/O=DOES_NOT_MATTER/C=US"`
4. Create the application-signing certificate in the Apple Developer page:
- Select `Developer ID Application` in Certificates, IDs & Profiles.
- Select `G2 Sub-CA (Xcode 11.4.1 or later)` and upload `developer-id.csr`.
5. If you want to notarize `pkg` or `app-in-pkg`, also create the installer-signing certificate in the same Apple UI:
- Select `Developer ID Installer` instead of `Developer ID Application`.
- Use the same CSR flow, then download that installer certificate too.
6. Export the certificates to `.p12` files:
- For the application certificate, convert it to PEM with `openssl x509 -inform DER -in developer-id-application.cer -out developer-id-application.pem -outform PEM`.
- Then export `developer-id-application.p12` with `openssl pkcs12 -export -inkey developer-id.key -in developer-id-application.pem -out developer-id-application.p12 -keypbe PBE-SHA1-3DES -certpbe PBE-SHA1-3DES -macalg sha1`.
- If you created the installer certificate, convert it too with `openssl x509 -inform DER -in developer-id-installer.cer -out developer-id-installer.pem -outform PEM`.
- Then export `developer-id-installer.p12` with `openssl pkcs12 -export -inkey developer-id.key -in developer-id-installer.pem -out developer-id-installer.p12 -keypbe PBE-SHA1-3DES -certpbe PBE-SHA1-3DES -macalg sha1`.
- OpenSSL will prompt for an `Export Password` each time; remember the exact password for each `.p12`, because those are the passwords later used for `security import` and GitHub Actions secrets.
7. Note your Team ID and Team Name from the Apple Developer account page at https://developer.apple.com/account
8. Create an app-specific password at https://appleid.apple.com/.

The certificates and the app-specific password can be reused for signing multiple apps and do not need to be regenerated for each app or release.

Now, you can either notarize on a local Mac or set up GitHub Actions for CI notarization.

### Option 1: Notarization on local macOS

1. Copy `developer-id-application.p12` onto the Mac. If you will notarize `pkg` or `app-in-pkg`, copy `developer-id-installer.p12` too.
2. Import the application certificate into the login keychain by double-clicking it, or run `security import developer-id-application.p12 -k ~/Library/Keychains/login.keychain-db -P "application-p12-password" -T /usr/bin/codesign -T /usr/bin/security`.
3. If you will notarize `pkg` or `app-in-pkg`, import the installer certificate too: `security import developer-id-installer.p12 -k ~/Library/Keychains/login.keychain-db -P "installer-p12-password" -T /usr/bin/productbuild -T /usr/bin/productsign -T /usr/bin/security`.
4. Store notarization credentials: `xcrun notarytool store-credentials easyinstaller-notary --apple-id "you@example.com" --team-id TEAMID1234 --password "app-specific-password"`.
5. Build with notarization: `easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg --output MyApp --app-name "My App" --app-exec myapp --mac-notarize --mac-notary-team-name "Example, Inc." --mac-notary-team-id TEAMID1234 --mac-notary-keychain-profile easyinstaller-notary`.

`MyApp.dmg` will be written in the current directory.

### Option 2: Notarization on GitHub runners

1. Base64-encode `developer-id-application.p12`:
- On Windows PowerShell, run `[Convert]::ToBase64String([IO.File]::ReadAllBytes("developer-id-application.p12")) | Set-Content -NoNewline developer-id-application.p12.base64`.
- On Linux or macOS, run `base64 developer-id-application.p12 > developer-id-application.p12.base64`.
2. If you want notarized `pkg` outputs, base64-encode `developer-id-installer.p12` too:
- On Windows PowerShell, run `[Convert]::ToBase64String([IO.File]::ReadAllBytes("developer-id-installer.p12")) | Set-Content -NoNewline developer-id-installer.p12.base64`.
- On Linux or macOS, run `base64 developer-id-installer.p12 > developer-id-installer.p12.base64`.
3. Before uploading secrets, verify that each `.p12` opens with its export password:
- Run `openssl pkcs12 -in developer-id-application.p12 -noout` and enter the application certificate export password.
- If you created the installer certificate, run `openssl pkcs12 -in developer-id-installer.p12 -noout` and enter the installer certificate export password.
- If either fails, regenerate that `.p12` and make sure you save the export password from that command.
4. Open your GitHub repository, then go to `Settings` > `Secrets and variables` > `Actions`.
5. Add these repository secrets:
- Set `MAC_CERTIFICATE_P12_BASE64` to the full contents of `developer-id-application.p12.base64`.
- Set `MAC_CERTIFICATE_PASSWORD` to the exact export password for `developer-id-application.p12`. **DO NOT USE YOUR APPLE ID PASSWORD, YOUR APP-SPECIFIC PASSWORD, OR ANY KEYCHAIN PASSWORD HERE!**
- If you want notarized `pkg` outputs, set `MAC_INSTALLER_CERTIFICATE_P12_BASE64` to the full contents of `developer-id-installer.p12.base64`, and set `MAC_INSTALLER_CERTIFICATE_PASSWORD` to the exact export password for `developer-id-installer.p12`.
- Set `MAC_NOTARY_APPLE_ID` to your Apple ID email.
- Set `MAC_NOTARY_TEAM_NAME` to your Apple Developer Team Name, for example `Example, Inc.`.
- Set `MAC_NOTARY_TEAM_ID` to your Apple Developer Team ID.
- Set `MAC_NOTARY_PASSWORD` to the app-specific password.  **DO NOT USE YOUR APPLE ID PASSWORD HERE!**
6. Run the workflow on `macos-latest` so the signing tools are available.
7. See the example workflow below, that will import the application certificate by default and only import the installer certificate when the pkg-specific secrets are present. The default example below still builds `MyApp.dmg` because that is the more typical end-user distribution format.

```yaml
- name: Import signing certificate
  env:
    MAC_CERTIFICATE_PASSWORD: ${{ secrets.MAC_CERTIFICATE_PASSWORD }}
    MAC_INSTALLER_CERTIFICATE_PASSWORD: ${{ secrets.MAC_INSTALLER_CERTIFICATE_PASSWORD }}
  run: |
    printf '%s' "${{ secrets.MAC_CERTIFICATE_P12_BASE64 }}" | base64 --decode > app-cert.p12
    openssl pkcs12 -in app-cert.p12 -passin env:MAC_CERTIFICATE_PASSWORD -noout >/dev/null
    openssl pkcs12 -in app-cert.p12 -passin env:MAC_CERTIFICATE_PASSWORD -nodes -out app-cert.pem
    openssl pkcs12 -export -in app-cert.pem -out app-cert-compat.p12 \
      -passout env:MAC_CERTIFICATE_PASSWORD \
      -keypbe PBE-SHA1-3DES \
      -certpbe PBE-SHA1-3DES \
      -macalg sha1
    security create-keychain -p "$RUNNER_TEMP" build.keychain
    security unlock-keychain -p "$RUNNER_TEMP" build.keychain
    security default-keychain -s build.keychain
    security import app-cert-compat.p12 -k build.keychain -P "$MAC_CERTIFICATE_PASSWORD" -T /usr/bin/codesign -T /usr/bin/security
    if [[ -n "${{ secrets.MAC_INSTALLER_CERTIFICATE_P12_BASE64 }}" && -n "$MAC_INSTALLER_CERTIFICATE_PASSWORD" ]]; then
      printf '%s' "${{ secrets.MAC_INSTALLER_CERTIFICATE_P12_BASE64 }}" | base64 --decode > installer-cert.p12
      openssl pkcs12 -in installer-cert.p12 -passin env:MAC_INSTALLER_CERTIFICATE_PASSWORD -noout >/dev/null
      openssl pkcs12 -in installer-cert.p12 -passin env:MAC_INSTALLER_CERTIFICATE_PASSWORD -nodes -out installer-cert.pem
      openssl pkcs12 -export -in installer-cert.pem -out installer-cert-compat.p12 \
        -passout env:MAC_INSTALLER_CERTIFICATE_PASSWORD \
        -keypbe PBE-SHA1-3DES \
        -certpbe PBE-SHA1-3DES \
        -macalg sha1
      security import installer-cert-compat.p12 -k build.keychain -P "$MAC_INSTALLER_CERTIFICATE_PASSWORD" -T /usr/bin/productbuild -T /usr/bin/productsign -T /usr/bin/security
    fi
    security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$RUNNER_TEMP" build.keychain
    security list-keychains -d user -s build.keychain

```yaml
- name: Build notarized package
  run: |
    easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg \
      --output MyApp \
      --app-name "My App" --app-exec myapp \
      --mac-notarize \
      --mac-notary-team-name "${{ secrets.MAC_NOTARY_TEAM_NAME }}" \
      --mac-notary-apple-id "${{ secrets.MAC_NOTARY_APPLE_ID }}" \
      --mac-notary-team-id "${{ secrets.MAC_NOTARY_TEAM_ID }}" \
      --mac-notary-password "${{ secrets.MAC_NOTARY_PASSWORD }}"
```

## Local validation tips

- Use `spctl --assess --type execute` for `.app` bundles. Running it against a standalone Mach-O binary commonly reports `valid but does not seem to be an app`, which is expected and does not mean the signature is bad.
- For standalone binaries inside `zip`, `tar.gz`, or a file-only `dmg`, validate the signature with `codesign --verify --verbose=4 --strict /path/to/binary`.
- Finder is the wrong launch path for a raw CLI executable. If you want double-click behavior on macOS, ship a `.app` bundle or a DMG containing a `.app` bundle.
- A `.app` launched from Finder does not get an attached terminal or interactive stdin. If the program waits on `std::cin`, it can appear to do nothing. The demo app avoids that by showing a dialog for normal launches and reserving `--headless` for CLI and CI checks.
