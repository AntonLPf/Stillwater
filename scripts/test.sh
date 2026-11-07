#!/usr/bin/env bash
#
# Runs ios-test's own tests, then the package's tests and the Example app's UI tests on one
# simulator, through ios-test.
#
#   scripts/test.sh                 the newest iPhone available
#   scripts/test.sh <simulator-id>  that simulator

set -euo pipefail
cd "$(dirname "$0")/.."

simulator=()
if [ $# -gt 0 ]; then
    simulator=(--simulator "$1")
fi

python3 scripts/tests/test_ios_test.py
scripts/ios-test quick --config .ios-test-package ${simulator[@]+"${simulator[@]}"}
scripts/ios-test quick ${simulator[@]+"${simulator[@]}"}
