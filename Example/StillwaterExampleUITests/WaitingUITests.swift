import Stillwater
import XCTest

final class WaitingUITests: ExampleUITestCase {
    private var lateRow: XCUIElement {
        app.staticTexts["home.lateRow"]
    }

    func testWaitUntilExistsSeesARowThatComesLate() {
        launch()
        XCTAssertFalse(lateRow.exists)

        app.buttons["home.showLateRow"].tap()

        XCTAssertTrue(lateRow.waitUntilExists(timeout: 5))
    }

    func testWaitUntilExistsGivesUpOnARowThatNeverComes() {
        launch()

        XCTAssertFalse(lateRow.waitUntilExists(timeout: 0.3))
    }

    func testWaitUntilGoneSeesARowLeave() {
        launch()
        app.buttons["home.showLateRow"].tap()
        XCTAssertTrue(lateRow.waitUntilExists(timeout: 5))

        app.buttons["home.hideLateRow"].tap()

        XCTAssertTrue(lateRow.waitUntilGone(timeout: 5))
    }

    func testFirstToExistSkipsWhatIsNotThere() {
        launch()
        let missing = app.buttons["home.noSuchButton"]
        let present = app.buttons["home.openSheet"]

        XCTAssertEqual([missing, present].firstToExist(timeout: 5)?.identifier, "home.openSheet")
    }

    func testFirstToExistReturnsNilWhenNothingComes() {
        launch()

        XCTAssertNil([app.buttons["home.noSuchButton"]].firstToExist(timeout: 0.3))
    }

    func testTapWhenSettledClosesASheetThatIsStillSliding() {
        launch()
        app.buttons["home.openSheet"].tap()
        let close = app.buttons["sheet.close"]
        XCTAssertTrue(close.waitUntilExists(timeout: 5))

        close.tapWhenSettled()

        XCTAssertTrue(close.waitUntilGone(timeout: 5))
    }
}
