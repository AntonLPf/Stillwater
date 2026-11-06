import Stillwater
import XCTest

final class StillwaterCaseUITests: ExampleUITestCase {
    func testLaunchAddsExtraArgumentsToTheOnesEveryTestHas() {
        launch(extraArguments: ["-example"])

        XCTAssertEqual(app.launchArguments, launchArguments + ["-example"])
    }

    func testTypeTextReachesTheField() {
        launch()
        let field = app.textFields["home.name"]
        field.tap()

        typeText("Ada", into: field)

        XCTAssertEqual(app.staticTexts["home.greeting"].label, "Hello, Ada")
    }

    func testDismissKeyboardClosesIt() {
        launch()
        let field = app.textFields["home.name"]
        field.tap()
        typeText("Ada", into: field)

        dismissKeyboard()

        XCTAssertTrue(app.keyboards.firstMatch.waitUntilGone(timeout: 2))
    }

    func testDismissKeyboardDoesNothingWithNoKeyboardUp() {
        launch()

        dismissKeyboard()

        XCTAssertTrue(app.navigationBars["Stillwater"].exists)
    }

    func testAuditLetsTheFilterIgnoreIssues() throws {
        launch()

        try auditAccessibility(ignoring: { _ in true })
    }

    /// A failed assertion ends the test, not the test runner. CI fails the run if the log says
    /// the runner restarted, which is what an async `setUp` in `StillwaterCase` caused.
    func testAFailedAssertionLeavesTheRunnerAlive() {
        launch()

        XCTExpectFailure("This failure is the test") {
            XCTFail("A failure with continueAfterFailure off")
        }
    }
}
