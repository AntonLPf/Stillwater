# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Until 1.0.0, a minor version can break
the API.

## [Unreleased]

### Added

- `scripts/ios-test`, a command that runs any iOS project's tests and checks the result.
- `ios-test` boots each simulator and puts its text size, appearance, and contrast back to the
  system's defaults before the tests, so a setting left behind cannot change the result.
- `ios-test` boots a simulator that is down, one at a time, and waits for the Mac to settle before
  the tests. It runs simulators in pairs, and shuts down a pair it booted before the next.
- `ios-test` gives each run its own result bundle in `test-logs/`.
- `ios-test` counts tests and lists failures from the result bundle, so a parameterized test counts
  once and a Swift Testing failure shows in its report.
- `ios-test --iterations` runs each test several times, and `--only` can be given more than once.
- `ios-test` runs unit tests without cloned simulators too.
- Tests for `scripts/ios-test` in `scripts/tests/`. They need no simulator, and `scripts/test.sh` runs
  them first.

## [0.1.1] - 2026-11-06

### Fixed

- `dismissKeyboard()` closes a keyboard that has not stopped moving after three seconds, instead of
  returning without closing it.

## [0.1.0] - 2026-11-06

### Added

- `waitUntilExists`, `waitUntilGone`, `waitUntilSettled`, and `tapWhenSettled` on `XCUIElement`.
- `firstToExist` on arrays of elements.
- `StillwaterCase`, a base test case with `launchArguments`, `waitUntilReady()`, and
  `launch(extraArguments:)`.
- `typeText(_:into:)`, `settledKeyboard()`, `canTapKey(_:)`, `dismissKeyboard()`, and
  `keyboardDismissKeys`.
- `auditAccessibility(for:ignoring:)`.
- `matching(identifier:label:)` on queries, and `NSPredicate.identifier(_:label:)`.

[Unreleased]: https://github.com/AntonLPf/Stillwater/compare/0.1.1...HEAD
[0.1.1]: https://github.com/AntonLPf/Stillwater/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/AntonLPf/Stillwater/releases/tag/0.1.0
