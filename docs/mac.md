# macOS guide

Use a macOS machine for mac targets.

## zip

Run: `easyinstaller --source ./build --os mac --arch arm64 --type zip --output MyApp-mac-arm64`.

`MyApp-mac-arm64.zip` will be written in the current directory.

## tar.gz

Run: `easyinstaller --source ./build --os mac --arch arm64 --type tar.gz --output MyApp-mac-arm64`.

`MyApp-mac-arm64.tar.gz` will be written in the current directory.

## dmg

Run: `easyinstaller --source ./build --os mac --arch arm64 --type dmg --output MyApp --app-name "My App"`.

`MyApp.dmg` will be written in the current directory.

## app

Run: `easyinstaller --source ./build --os mac --arch arm64 --type app --output MyApp --app-name "My App" --app-exec myapp`.

`MyApp.app` will be written in the current directory.

## app-in-dmg

Run: `easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg --output MyApp --app-name "My App" --app-exec myapp`.

`MyApp.dmg` will be written in the current directory.

## Notarization

### Common setup

1. Join the Apple Developer Program: https://developer.apple.com/programs/.
2. Open Certificates, IDs & Profiles: https://developer.apple.com/account/resources/certificates/list.
3. Generate a private key and CSR on any machine: `openssl genrsa -out developer-id.key 2048` then `openssl req -new -key developer-id.key -out developer-id.csr -subj "/CN=Your Name/OU=Your Org/O=Your Company/C=US"`.
4. Create a `Developer ID Application` certificate in the Apple Developer page and upload `developer-id.csr`.
5. Download the certificate, convert it to PEM with `openssl x509 -inform DER -in developer-id.cer -out developer-id.pem -outform PEM`, then export a `.p12` with `openssl pkcs12 -export -inkey developer-id.key -in developer-id.pem -out developer-id.p12`.
6. Note your Team ID from the Apple Developer account page.
7. Create an app-specific password at https://appleid.apple.com/.

Now, you can either notarize on a local Mac or set up GitHub Actions for CI notarization.

### Notarization on local macOS

1. Copy `developer-id.p12` onto the Mac.
2. Import it into the login keychain by double-clicking it, or run `security import developer-id.p12 -k ~/Library/Keychains/login.keychain-db -P "p12-password" -T /usr/bin/codesign -T /usr/bin/security`.
3. Store notarization credentials: `xcrun notarytool store-credentials easyinstaller-notary --apple-id "you@example.com" --team-id TEAMID1234 --password "app-specific-password"`.
4. Build with notarization: `easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg --output MyApp --app-name "My App" --app-exec myapp --mac-notarize --mac-sign-identity "Developer ID Application: Example, Inc. (TEAMID1234)" --mac-notary-keychain-profile easyinstaller-notary`.

`MyApp.dmg` will be written in the current directory.

### Notarization on GitHub runners

1. Base64-encode `developer-id.p12`:
- On Windows PowerShell, run `[Convert]::ToBase64String([IO.File]::ReadAllBytes("developer-id.p12")) | Set-Content -NoNewline developer-id.p12.base64`.
- On Linux or macOS, run `base64 developer-id.p12 > developer-id.p12.base64`.
2. On Windows PowerShell, run `[Convert]::ToBase64String([IO.File]::ReadAllBytes("developer-id.p12")) | Set-Content -NoNewline developer-id.p12.base64`.
3. On Linux or macOS, run `base64 developer-id.p12 > developer-id.p12.base64`.
4. Open your GitHub repository, then go to `Settings` > `Secrets and variables` > `Actions`.
5. Add these repository secrets:
- Set `MAC_CERTIFICATE_P12_BASE64` to the full contents of `developer-id.p12.base64`.
- Set `MAC_CERTIFICATE_PASSWORD` to the password you used when creating `developer-id.p12`.
- Set `MAC_SIGN_IDENTITY` to the full signing identity string. This follows a strict format: `Developer ID Application - [Team Name] ([Team ID])`.
- Set `MAC_NOTARY_APPLE_ID` to your Apple ID email.
- Set `MAC_NOTARY_TEAM_ID` to your Apple Developer Team ID.
- Set `MAC_NOTARY_PASSWORD` to the app-specific password.
6. Run the workflow on `macos-latest` so the signing tools are available.
7. Pass the notarization credentials directly to easyinstaller with `--mac-notary-apple-id`, `--mac-notary-team-id`, and `--mac-notary-password`.

This workflow will write the notarized artifact in the runner workspace, for example `./MyApp.dmg`.

```yaml
- name: Import signing certificate
  run: |
    echo "$MAC_CERTIFICATE_P12_BASE64" | base64 --decode > cert.p12
    security create-keychain -p "$RUNNER_TEMP" build.keychain
    security unlock-keychain -p "$RUNNER_TEMP" build.keychain
    security default-keychain -s build.keychain
    security import cert.p12 -k build.keychain -P "$MAC_CERTIFICATE_PASSWORD" -T /usr/bin/codesign -T /usr/bin/security
    security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$RUNNER_TEMP" build.keychain
    security list-keychains -d user -s build.keychain
  env:
    MAC_CERTIFICATE_P12_BASE64: ${{ secrets.MAC_CERTIFICATE_P12_BASE64 }}
    MAC_CERTIFICATE_PASSWORD: ${{ secrets.MAC_CERTIFICATE_PASSWORD }}

- name: Build notarized package
  run: |
    easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg \
      --output MyApp \
      --app-name "My App" --app-exec myapp \
      --mac-notarize \
      --mac-sign-identity "$MAC_SIGN_IDENTITY" \
      --mac-notary-apple-id "$MAC_NOTARY_APPLE_ID" \
      --mac-notary-team-id "$MAC_NOTARY_TEAM_ID" \
      --mac-notary-password "$MAC_NOTARY_PASSWORD"
  env:
    MAC_SIGN_IDENTITY: ${{ secrets.MAC_SIGN_IDENTITY }}
    MAC_NOTARY_APPLE_ID: ${{ secrets.MAC_NOTARY_APPLE_ID }}
    MAC_NOTARY_TEAM_ID: ${{ secrets.MAC_NOTARY_TEAM_ID }}
    MAC_NOTARY_PASSWORD: ${{ secrets.MAC_NOTARY_PASSWORD }}
```
