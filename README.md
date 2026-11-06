# Stillwater

XCUITest helpers that act only when the screen holds still.

UI tests usually fail in one of two ways. They wait too long, because XCTest's
`waitForExistence(timeout:)` checks about once a second even when the element is already there.
Or they act too soon, tapping a button in a sheet that is still sliding. Stillwater fixes both,
and gives every app the same base test case.

In the app Stillwater came from, that one-second floor was about 40% of a UI test run.

```swift
import Stillwater
import XCTest

final class CheckoutUITests: AppUITestCase {
    func testPay() {
        launch()
        app.buttons["cart.checkout"].tap()

        let pay = app.buttons["checkout.pay"]
        XCTAssertTrue(pay.waitUntilExists(timeout: 5)) // Returns as soon as it is there.
        pay.tapWhenSettled()                           // Waits for the sheet to stop moving.

        XCTAssertTrue(pay.waitUntilGone(timeout: 5))
    }
}
```

## Install

In Xcode, choose **File > Add Package Dependencies**, enter
`https://github.com/AntonLPf/Stillwater.git`, and add the library to your **UI test target** only,
not your app.

## Use it

Subclass `StillwaterCase` once per app:

```swift
class AppUITestCase: StillwaterCase {
    override var launchArguments: [String] { ["-demo", "-AppleLanguages", "(en)"] }

    override func waitUntilReady() {
        XCTAssertTrue(app.navigationBars["Home"].waitUntilExists(timeout: 10))
    }
}
```

`launch()` starts the app and calls `waitUntilReady()`. `launch(extraArguments:)` adds arguments
for one test.

> [!IMPORTANT]
> Override `setUpWithError()`, not `setUp() async`. With the async one, every failed assertion
> ends the test runner's process and the run restarts. The tests can still look green; only the
> log says `Restarting after unexpected exit`.

## What is in it

| Helper | What it does |
| --- | --- |
| `waitUntilExists(timeout:)` | Checks at once, then every tenth of a second. |
| `waitUntilGone(timeout:)` | The same, until the element is gone. |
| `waitUntilSettled(timeout:)` | Waits until the element's frame is the same on two checks in a row. |
| `tapWhenSettled()` | Taps once the element holds still, or after two seconds as it is. |
| `[a, b].firstToExist(timeout:)` | Waits once for whichever query matches, for a control that changes type between systems. |
| `typeText(_:into:)` | Types, then waits for the keyboard to stand still. |
| `settledKeyboard(timeout:)` | The keyboard once it holds still, or nil. |
| `dismissKeyboard()` | Closes the keyboard, with a fallback for iPad on iOS 27. Override `keyboardDismissKeys` for other key names. |
| `canTapKey(_:)` | Says no instead of failing when a key reports a frame off screen. |
| `auditAccessibility(for:ignoring:)` | Runs the system audit, with a filter for issues you accept. |
| `query.matching(identifier:label:)` | Picks one of several rows that share an identifier. |

## Run tests the same way everywhere

`scripts/ios-test` is a command for any iOS project, separate from the package. Link it onto your
`PATH` once:

```bash
ln -s "$PWD/scripts/ios-test" /usr/local/bin/ios-test
```

Put the settings in `.ios-test` at the root of each project:

```
PROJECT=App.xcodeproj
SCHEME=App
UI_TESTS=AppUITests
UNIT_TESTS=AppTests
```

Then run it there:

| Command | What it runs |
| --- | --- |
| `ios-test quick` | The UI tests on one iPhone. |
| `ios-test close` | All tests on an iPhone and an iPad on the newest iOS that has both. |
| `ios-test release` | The same, and every simulator in `RELEASE_SIMULATORS`. |

It picks the simulators, runs at most two at a time, keeps the full logs in `test-logs/`, and prints
a table. It fails if the test runner restarted or no test ran, which `xcodebuild` reports as
success. `ios-test --help` lists the rest.

A simulator keeps its text size, appearance, and contrast after a person or another project changes
them, so `ios-test` boots each one and puts them back to the system's defaults before the tests. It
prints any setting it changes.

## Requirements

iOS 18 or later, and Swift 6 tools (Xcode 16 or later). Developed with Xcode 27.2, and tested on
iPhone and iPad simulators with iOS 18.5, 26.2, and 27.0.

## Example

`Example/` is a small app with UI tests for every helper. Open
`Example/StillwaterExample.xcodeproj`, or run everything with:

```bash
scripts/test.sh
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are listed in [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE).
