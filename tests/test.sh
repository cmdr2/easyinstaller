#!/usr/bin/env bash
#
# Test suite for easy-installer.sh
#
# Run: bash tests/test.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="${SCRIPT_DIR}/easy-installer.sh"
TEST_DIR="$(mktemp -d /tmp/easy-installer-test-XXXXXX)"
PASS=0
FAIL=0

cleanup() { rm -rf "$TEST_DIR"; }
trap cleanup EXIT

##############################################################################
# Helpers
##############################################################################
setup_source() {
    local src="${TEST_DIR}/source"
    rm -rf "$src"
    mkdir -p "$src/subdir"
    echo "hello world" > "$src/hello.txt"
    echo '#!/bin/bash' > "$src/myapp"
    echo 'echo "running"' >> "$src/myapp"
    chmod +x "$src/myapp"
    echo "nested file" > "$src/subdir/nested.txt"
    echo "$src"
}

assert_eq() {
    local desc="$1" expected="$2" actual="$3"
    if [[ "$expected" == "$actual" ]]; then
        echo "  PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc (expected: '$expected', got: '$actual')"
        FAIL=$((FAIL + 1))
    fi
}

assert_file_exists() {
    local desc="$1" path="$2"
    if [[ -e "$path" ]]; then
        echo "  PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc (file not found: $path)"
        FAIL=$((FAIL + 1))
    fi
}

assert_exit_code() {
    local desc="$1" expected="$2"
    shift 2
    local actual=0
    "$@" >/dev/null 2>&1 || actual=$?
    if [[ "$expected" -eq "$actual" ]]; then
        echo "  PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc (expected exit $expected, got $actual)"
        FAIL=$((FAIL + 1))
    fi
}

assert_output_contains() {
    local desc="$1" pattern="$2"
    shift 2
    local output
    output="$("$@" 2>&1)" || true
    if echo "$output" | grep -q "$pattern"; then
        echo "  PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc (output did not contain '$pattern')"
        FAIL=$((FAIL + 1))
    fi
}

##############################################################################
# Tests
##############################################################################
echo "=== Testing: --help and --version ==="

assert_exit_code "--help exits 0" 0 "$SCRIPT" --help
assert_exit_code "--version exits 0" 0 "$SCRIPT" --version
assert_output_contains "--version shows version" "easy-installer v" "$SCRIPT" --version
assert_output_contains "--help shows usage" "USAGE" "$SCRIPT" --help

echo ""
echo "=== Testing: Argument validation ==="

assert_exit_code "Missing --source fails" 1 "$SCRIPT" --os linux --arch x86_64 --type zip --output test
assert_exit_code "Missing --os fails" 1 "$SCRIPT" --source /tmp --arch x86_64 --type zip --output test
assert_exit_code "Missing --arch fails" 1 "$SCRIPT" --source /tmp --os linux --type zip --output test
assert_exit_code "Missing --type fails" 1 "$SCRIPT" --source /tmp --os linux --arch x86_64 --output test
assert_exit_code "Missing --output fails" 1 "$SCRIPT" --source /tmp --os linux --arch x86_64 --type zip
assert_exit_code "Invalid OS fails" 1 "$SCRIPT" --source /tmp --os bsd --arch x86_64 --type zip --output test
assert_exit_code "Invalid arch fails" 1 "$SCRIPT" --source /tmp --os linux --arch sparc --type zip --output test
assert_exit_code "Invalid type fails" 1 "$SCRIPT" --source /tmp --os linux --arch x86_64 --type msi --output test
assert_exit_code "Invalid OS+type combo fails" 1 "$SCRIPT" --source /tmp --os windows --arch x86_64 --type deb --output test
assert_exit_code "Unknown option fails" 1 "$SCRIPT" --bogus

echo ""
echo "=== Testing: OS aliases ==="

SRC="$(setup_source)"

assert_exit_code "'win' alias works" 0 "$SCRIPT" --source "$SRC" --os win --arch x86_64 --type zip --output "${TEST_DIR}/alias-win"
assert_exit_code "'macos' alias works" 0 "$SCRIPT" --source "$SRC" --os macos --arch x86_64 --type zip --output "${TEST_DIR}/alias-mac"

echo ""
echo "=== Testing: Arch aliases ==="

assert_exit_code "'amd64' alias works" 0 "$SCRIPT" --source "$SRC" --os linux --arch amd64 --type zip --output "${TEST_DIR}/alias-amd64"
assert_exit_code "'x64' alias works" 0 "$SCRIPT" --source "$SRC" --os linux --arch x64 --type zip --output "${TEST_DIR}/alias-x64"
assert_exit_code "'aarch64' alias works" 0 "$SCRIPT" --source "$SRC" --os linux --arch aarch64 --type zip --output "${TEST_DIR}/alias-aarch64"

echo ""
echo "=== Testing: zip ==="

SRC="$(setup_source)"
cd "$TEST_DIR"
"$SCRIPT" --source "$SRC" --os linux --arch x86_64 --type zip --output "${TEST_DIR}/test-linux-zip"
assert_file_exists "zip file created" "${TEST_DIR}/test-linux-zip.zip"

# Verify contents
EXTRACT_DIR="${TEST_DIR}/extract-zip"
mkdir -p "$EXTRACT_DIR"
unzip -q "${TEST_DIR}/test-linux-zip.zip" -d "$EXTRACT_DIR"
assert_file_exists "zip contains hello.txt" "${EXTRACT_DIR}/source/hello.txt"
assert_file_exists "zip contains nested file" "${EXTRACT_DIR}/source/subdir/nested.txt"
assert_eq "zip preserves content" "hello world" "$(cat "${EXTRACT_DIR}/source/hello.txt")"

echo ""
echo "=== Testing: tar.gz ==="

SRC="$(setup_source)"
"$SCRIPT" --source "$SRC" --os linux --arch x86_64 --type tar.gz --output "${TEST_DIR}/test-linux-tgz"
assert_file_exists "tar.gz file created" "${TEST_DIR}/test-linux-tgz.tar.gz"

# Verify contents
EXTRACT_DIR="${TEST_DIR}/extract-tgz"
mkdir -p "$EXTRACT_DIR"
tar -xzf "${TEST_DIR}/test-linux-tgz.tar.gz" -C "$EXTRACT_DIR"
assert_file_exists "tar.gz contains hello.txt" "${EXTRACT_DIR}/source/hello.txt"
assert_file_exists "tar.gz contains nested file" "${EXTRACT_DIR}/source/subdir/nested.txt"
assert_eq "tar.gz preserves content" "hello world" "$(cat "${EXTRACT_DIR}/source/hello.txt")"

echo ""
echo "=== Testing: tar.gz type aliases ==="

SRC="$(setup_source)"
assert_exit_code "'targz' alias works" 0 "$SCRIPT" --source "$SRC" --os linux --arch x86_64 --type targz --output "${TEST_DIR}/alias-targz"
assert_exit_code "'tgz' alias works" 0 "$SCRIPT" --source "$SRC" --os linux --arch x86_64 --type tgz --output "${TEST_DIR}/alias-tgz"

echo ""
echo "=== Testing: deb ==="

if command -v dpkg-deb >/dev/null 2>&1; then
    SRC="$(setup_source)"
    "$SCRIPT" --source "$SRC" --os linux --arch x86_64 --type deb --output "${TEST_DIR}/test-pkg" \
        --app-name "TestApp" --app-version "2.0.0" --app-exec myapp --app-maintainer "test@test.com"
    assert_file_exists "deb file created" "${TEST_DIR}/test-pkg.deb"

    # Verify metadata
    DEB_INFO="$(dpkg-deb --info "${TEST_DIR}/test-pkg.deb")"
    assert_eq "deb arch is amd64" "true" "$(echo "$DEB_INFO" | grep -q 'Architecture: amd64' && echo true || echo false)"
    assert_eq "deb version is 2.0.0" "true" "$(echo "$DEB_INFO" | grep -q 'Version: 2.0.0' && echo true || echo false)"
else
    echo "  SKIP: dpkg-deb not available"
fi

echo ""
echo "=== Testing: .app bundle ==="

SRC="$(setup_source)"
"$SCRIPT" --source "$SRC" --os mac --arch arm64 --type app --output "${TEST_DIR}/TestApp" \
    --app-name "TestApp" --app-version "1.2.3" --app-exec myapp
assert_file_exists ".app bundle created" "${TEST_DIR}/TestApp.app"
assert_file_exists ".app Info.plist exists" "${TEST_DIR}/TestApp.app/Contents/Info.plist"
assert_file_exists ".app MacOS launcher exists" "${TEST_DIR}/TestApp.app/Contents/MacOS/myapp"
assert_file_exists ".app Resources copied" "${TEST_DIR}/TestApp.app/Contents/Resources/hello.txt"

# Verify Info.plist content
assert_eq "Info.plist has correct version" "true" \
    "$(grep -q '1.2.3' "${TEST_DIR}/TestApp.app/Contents/Info.plist" && echo true || echo false)"
assert_eq "Info.plist has correct name" "true" \
    "$(grep -q 'TestApp' "${TEST_DIR}/TestApp.app/Contents/Info.plist" && echo true || echo false)"

echo ""
echo "=== Testing: NSIS (if makensis available) ==="

if command -v makensis >/dev/null 2>&1; then
    SRC="$(setup_source)"
    "$SCRIPT" --source "$SRC" --os windows --arch x86_64 --type nsis --output "${TEST_DIR}/test-setup" \
        --app-name "TestApp" --app-version "1.0.0"
    assert_file_exists "NSIS installer created" "${TEST_DIR}/test-setup.exe"
else
    echo "  SKIP: makensis not available"
fi

echo ""
echo "=== Testing: RPM (if rpmbuild available) ==="

if command -v rpmbuild >/dev/null 2>&1; then
    SRC="$(setup_source)"
    "$SCRIPT" --source "$SRC" --os linux --arch x86_64 --type rpm --output "${TEST_DIR}/test-pkg" \
        --app-name "TestApp" --app-version "1.0.0"
    assert_file_exists "RPM file created" "${TEST_DIR}/test-pkg.rpm"
else
    echo "  SKIP: rpmbuild not available"
fi

echo ""
echo "============================================"
echo "Results: ${PASS} passed, ${FAIL} failed"
echo "============================================"

[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
