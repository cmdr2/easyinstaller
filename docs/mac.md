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

## Notarization

*You can skip the 'Common setup' section if you already have a valid Developer ID Application certificate and an app-specific password.*

`--mac-notarize` is supported for mac types `zip`, `dmg`, `app`, and `app-in-dmg`. It is not supported for `tar.gz`.

### Common setup

1. Join the Apple Developer Program: https://developer.apple.com/programs/.
2. Open Certificates, IDs & Profiles: https://developer.apple.com/account/resources/certificates/list.
3. Generate a private key and CSR on any machine:
- `openssl genrsa -out developer-id.key 2048`
- `openssl req -new -key developer-id.key -out developer-id.csr -subj "/CN=DOES_NOT_MATTER/OU=DOES_NOT_MATTER/O=DOES_NOT_MATTER/C=US"`
4. Create a `Developer ID Application` certificate in the Apple Developer page, select `G2 Sub-CA (Xcode 11.4.1 or later)` and upload `developer-id.csr`.
5. Download the certificate as `developer-id.cer`, then
- convert it to PEM with `openssl x509 -inform DER -in developer-id.cer -out developer-id.pem -outform PEM`
- then export a `.p12` with `openssl pkcs12 -export -inkey developer-id.key -in developer-id.pem -out developer-id.p12 -keypbe PBE-SHA1-3DES -certpbe PBE-SHA1-3DES -macalg sha1`
- OpenSSL will prompt for an `Export Password`; remember that exact password, because it is the password for `developer-id.p12` and must later be used for `MAC_CERTIFICATE_PASSWORD` and `security import`
6. Note your Team ID from the Apple Developer account page at https://developer.apple.com/account
7. Create an app-specific password at https://appleid.apple.com/.

The certificate and the app-specific password can be reused for signing multiple apps and does not need to be regenerated for each app or release.

Now, you can either notarize on a local Mac or set up GitHub Actions for CI notarization.

### Option 1: Notarization on local macOS

1. Copy `developer-id.p12` onto the Mac.
2. Import it into the login keychain by double-clicking it, or run `security import developer-id.p12 -k ~/Library/Keychains/login.keychain-db -P "p12-password" -T /usr/bin/codesign -T /usr/bin/security`.
3. Store notarization credentials: `xcrun notarytool store-credentials easyinstaller-notary --apple-id "you@example.com" --team-id TEAMID1234 --password "app-specific-password"`.
4. Build with notarization: `easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg --output MyApp --app-name "My App" --app-exec myapp --mac-notarize --mac-sign-identity "Developer ID Application: Example, Inc. (TEAMID1234)" --mac-notary-keychain-profile easyinstaller-notary`.

`MyApp.dmg` will be written in the current directory.

### Option 2: Notarization on GitHub runners

1. Base64-encode `developer-id.p12`:
- On Windows PowerShell, run `[Convert]::ToBase64String([IO.File]::ReadAllBytes("developer-id.p12")) | Set-Content -NoNewline developer-id.p12.base64`.
- On Linux or macOS, run `base64 developer-id.p12 > developer-id.p12.base64`.
2. Before uploading secrets, verify that the `.p12` opens with the export password you chose in the `openssl pkcs12 -export` step:
- Run `openssl pkcs12 -in developer-id.p12 -noout` and enter the export password when prompted.
- If this fails, regenerate `developer-id.p12` and make sure you save the export password from that command.
3. Open your GitHub repository, then go to `Settings` > `Secrets and variables` > `Actions`.
4. Add these repository secrets:
- Set `MAC_CERTIFICATE_P12_BASE64` to the full contents of `developer-id.p12.base64`.
- Set `MAC_CERTIFICATE_PASSWORD` to the exact `Export Password` that `openssl pkcs12 -export` asked for when you created `developer-id.p12`. **DO NOT USE YOUR APPLE ID PASSWORD, YOUR APP-SPECIFIC PASSWORD, OR ANY KEYCHAIN PASSWORD HERE!**
- Set `MAC_NOTARY_APPLE_ID` to your Apple ID email.
- Set `MAC_NOTARY_TEAM_NAME` to your Apple Developer Team Name, for example `Example, Inc.`.
- Set `MAC_NOTARY_TEAM_ID` to your Apple Developer Team ID.
- Set `MAC_NOTARY_PASSWORD` to the app-specific password.  **DO NOT USE YOUR APPLE ID PASSWORD HERE!**
5. Run the workflow on `macos-latest` so the signing tools are available.
6. If you change the workflow YAML itself, start a fresh workflow run from a new commit or `workflow_dispatch`; GitHub re-runs keep the original run's `GITHUB_SHA` and `GITHUB_REF`, so a re-run will not pick up newer workflow-file changes.
7. See the example workflow below, that will use these secrets to import the certificate and notarize the app during the build step. It will write `MyApp.dmg` in the current directory.

```yaml
- name: Import signing certificate
  env:
    MAC_CERTIFICATE_PASSWORD: ${{ secrets.MAC_CERTIFICATE_PASSWORD }}
  run: |
    printf '%s' "${{ secrets.MAC_CERTIFICATE_P12_BASE64 }}" | base64 --decode > cert.p12
    openssl pkcs12 -in cert.p12 -passin env:MAC_CERTIFICATE_PASSWORD -noout >/dev/null
    openssl pkcs12 -in cert.p12 -passin env:MAC_CERTIFICATE_PASSWORD -nodes -out cert.pem
    openssl pkcs12 -export -in cert.pem -out cert-compat.p12 \
      -passout env:MAC_CERTIFICATE_PASSWORD \
      -keypbe PBE-SHA1-3DES \
      -certpbe PBE-SHA1-3DES \
      -macalg sha1
    security create-keychain -p "$RUNNER_TEMP" build.keychain
    security unlock-keychain -p "$RUNNER_TEMP" build.keychain
    security default-keychain -s build.keychain
    security import cert-compat.p12 -k build.keychain -P "$MAC_CERTIFICATE_PASSWORD" -T /usr/bin/codesign -T /usr/bin/security
    security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$RUNNER_TEMP" build.keychain
    security list-keychains -d user -s build.keychain
```


The step-local `env` is intentional here: it preserves the password exactly for tools like `openssl` even when the password contains shell-significant characters such as `$`, quotes, or backslashes.

```yaml
- name: Build notarized package
  run: |
    easyinstaller --source ./build --os mac --arch arm64 --type app-in-dmg \
      --output MyApp \
      --app-name "My App" --app-exec myapp \
      --mac-notarize \
      --mac-sign-identity "Developer ID Application: ${{ secrets.MAC_NOTARY_TEAM_NAME }} (${{ secrets.MAC_NOTARY_TEAM_ID }})" \
      --mac-notary-apple-id "${{ secrets.MAC_NOTARY_APPLE_ID }}" \
      --mac-notary-team-id "${{ secrets.MAC_NOTARY_TEAM_ID }}" \
      --mac-notary-password "${{ secrets.MAC_NOTARY_PASSWORD }}"
```
