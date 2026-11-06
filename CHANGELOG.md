# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Until 1.0.0, a minor version can break
the API.

## [Unreleased]

### Added

- `waitUntilExists`, `waitUntilGone`, `waitUntilSettled`, and `tapWhenSettled` on `XCUIElement`.
- `firstToExist` on arrays of elements.
- `StillwaterCase`, a base test case with `launchArguments`, `waitUntilReady()`, and
  `launch(extraArguments:)`.
- `typeText(_:into:)`, `settledKeyboard()`, `canTapKey(_:)`, `dismissKeyboard()`, and
  `keyboardDismissKeys`.
- `auditAccessibility(for:ignoring:)`.
- `matching(identifier:label:)` on queries, and `NSPredicate.identifier(_:label:)`.
