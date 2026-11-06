#!/usr/bin/env bash
#
# Runs the package's tests and the Example app's UI tests on one simulator.
#
#   scripts/test.sh                 the newest iPhone available
#   scripts/test.sh <simulator-id>  that simulator
#
# xcodebuild can report success in two cases this script does not accept: when the test runner
# died and restarted, and when no test ran at all.

set -euo pipefail
cd "$(dirname "$0")/.."

simulator="${1:-$(xcrun simctl list devices available -j | python3 -c '
import json, re, sys
devices = json.load(sys.stdin)["devices"]
phones = [
    (tuple(int(part) for part in re.findall(r"iOS-(\d+)-(\d+)", runtime)[0]), device["udid"])
    for runtime, entries in devices.items() if "iOS" in runtime
    for device in entries if re.fullmatch(r"iPhone \d+.*", device["name"])
]
print(max(phones)[1])
')}"
echo "Simulator: $simulator"

log="$(mktemp)"
trap 'rm -f "$log"' EXIT

run() {
    local status=0
    "$@" > "$log" 2>&1 || status=$?
    grep -E "error:|Executed [0-9]+ test|\*\* TEST" "$log" || true
    if [ "$status" -ne 0 ]; then
        echo "error: xcodebuild failed; see the lines above" >&2
        exit "$status"
    fi
    if grep -q "Restarting after unexpected exit" "$log"; then
        echo "error: the test runner restarted during the run" >&2
        exit 1
    fi
    if ! grep -qE "Executed [1-9][0-9]* test" "$log"; then
        echo "error: no test ran" >&2
        exit 1
    fi
}

run xcodebuild test -scheme Stillwater -destination "id=$simulator"

run xcodebuild test \
    -project Example/StillwaterExample.xcodeproj \
    -scheme StillwaterExample \
    -destination "id=$simulator" \
    -parallel-testing-enabled NO
