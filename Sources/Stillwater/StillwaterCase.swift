import XCTest

/// A base class for UI tests that wait for the screen to hold still before they act.
///
/// Subclass it per app. Say how the app launches with `launchArguments` and what "ready"
/// means with `waitUntilReady()`; the rest is shared.
@MainActor
open class StillwaterCase: XCTestCase {
    public private(set) var app: XCUIApplication!

    /// Launch arguments every test starts with. Override to add the app's own.
    open var launchArguments: [String] { [] }

    /// Keyboard buttons `dismissKeyboard()` tries, in order, before it falls back to Return.
    open var keyboardDismissKeys: [String] {
        ["search", "Search", "done", "Done", "return", "Return"]
    }

    /// Called after `launch(extraArguments:)`. Override to wait for the app's first screen.
    open func waitUntilReady() {}

    open override func setUp() async throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = launchArguments
    }

    /// Launches the app with `extraArguments` appended, then waits until it is ready.
    public func launch(extraArguments: [String] = []) {
        app.launchArguments += extraArguments
        app.launch()
        waitUntilReady()
    }

    /// Runs the system accessibility audit on the current screen.
    public func auditAccessibility(
        for types: XCUIAccessibilityAuditType = [.elementDetection, .sufficientElementDescription, .trait]
    ) throws {
        try app.performAccessibilityAudit(for: types)
    }
}
