# Stillwater

XCUITest helpers that act only when the screen holds still.

Work in progress.

- Waits that check at once and then every tenth of a second, instead of XCTest's once-a-second polling.
- `waitUntilSettled` and `tapWhenSettled`: wait for a sheet, alert, or keyboard to stop moving before acting.
- `StillwaterCase`: a base test case with keyboard handling that survives iOS 27 on iPad.

## Requirements

iOS 18+, Xcode 16+, Swift 6.

## License

MIT
