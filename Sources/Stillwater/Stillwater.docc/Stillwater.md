# ``Stillwater``

XCUITest helpers that act only when the screen holds still.

## Overview

Subclass ``StillwaterCase`` once per app. Say how the app launches and what "ready" means, then
write tests with waits that return as soon as they can and taps that hold off until a sheet stops
moving.

```swift
class AppUITestCase: StillwaterCase {
    override var launchArguments: [String] { ["-demo"] }

    override func waitUntilReady() {
        XCTAssertTrue(app.navigationBars["Home"].waitUntilExists(timeout: 10))
    }
}
```

Override `setUpWithError()` in your subclasses, not `setUp() async`. With the async one, every
failed assertion ends the test runner's process.

## Topics

### Test cases

- ``StillwaterCase``
