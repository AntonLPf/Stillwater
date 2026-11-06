import XCTest
@testable import Stillwater

@MainActor
final class PollTests: XCTestCase {
    func testReturnsAtOnceWhenTheConditionAlreadyHolds() {
        let start = Date()
        XCTAssertTrue(poll(5) { true })
        XCTAssertLessThan(Date().timeIntervalSince(start), 0.05)
    }

    func testReturnsAsSoonAsTheConditionStartsToHold() {
        var checks = 0
        XCTAssertTrue(poll(5, interval: 0.01) {
            checks += 1
            return checks == 3
        })
        XCTAssertEqual(checks, 3)
    }

    func testGivesUpAfterTheTimeout() {
        let start = Date()
        XCTAssertFalse(poll(0.2, interval: 0.01) { false })
        XCTAssertGreaterThanOrEqual(Date().timeIntervalSince(start), 0.2)
    }

    func testChecksOnceEvenWithNoTime() {
        var checks = 0
        XCTAssertFalse(poll(0) { checks += 1; return false })
        XCTAssertEqual(checks, 1)
    }
}
