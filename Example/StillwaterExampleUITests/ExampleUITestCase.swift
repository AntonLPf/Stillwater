import Stillwater
import XCTest

/// What every app adds to `StillwaterCase`: how it launches, and what "ready" means.
class ExampleUITestCase: StillwaterCase {
    override var launchArguments: [String] {
        ["-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
    }

    override func waitUntilReady() {
        XCTAssertTrue(app.navigationBars["Stillwater"].waitUntilExists(timeout: 10), "Expected the home screen")
    }
}
