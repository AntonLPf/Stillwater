import XCTest

// XCTest's `waitForExistence(timeout:)` and `waitForNonExistence(timeout:)` evaluate about once a
// second, so a wait for an element that is already on screen still takes a second. These check at
// once and then every tenth of a second.
@MainActor
extension XCUIElement {
    /// Whether the element exists within `timeout`, returning as soon as it does.
    public func waitUntilExists(timeout: TimeInterval) -> Bool {
        poll(timeout) { exists }
    }

    /// Whether the element is gone within `timeout`, returning as soon as it is.
    public func waitUntilGone(timeout: TimeInterval) -> Bool {
        poll(timeout) { !exists }
    }

    /// Whether the element is on screen and holds still within `timeout`: its frame is the
    /// same on two checks in a row. A wait that returns at once can act on a sheet or an
    /// alert that is still sliding.
    public func waitUntilSettled(timeout: TimeInterval) -> Bool {
        var last = CGRect.null
        return poll(timeout) {
            let frame = exists ? self.frame : .null
            defer { last = frame }
            return !frame.isEmpty && frame == last
        }
    }

    /// Taps the element once it holds still, or after two seconds as it is.
    public func tapWhenSettled() {
        _ = waitUntilSettled(timeout: 2)
        tap()
    }
}

@MainActor
extension Array where Element == XCUIElement {
    /// The first of these elements to exist within `timeout`, checked in order on each pass. A
    /// lookup that tries several queries waits once, not once per query that is not there.
    public func firstToExist(timeout: TimeInterval) -> XCUIElement? {
        var found: XCUIElement?
        _ = poll(timeout) {
            found = first { $0.exists }
            return found != nil
        }
        return found
    }
}
