# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Until 1.0.0, a minor version can break
the API.

## [Unreleased]

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

[Unreleased]: https://github.com/AntonLPf/Stillwater/compare/0.1.0...HEAD
[0.1.0]: https://github.com/AntonLPf/Stillwater/releases/tag/0.1.0
