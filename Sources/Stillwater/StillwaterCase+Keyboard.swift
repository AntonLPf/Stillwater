import XCTest

extension StillwaterCase {
    /// Types into a field that has focus, then waits for the keyboard to stand still. On
    /// iOS 27 an iPad can hide the software keyboard while `typeText` types and bring it
    /// back a second later, after the app is idle, and the sheet or alert moves with it.
    public func typeText(_ text: String, into field: XCUIElement) {
        field.typeText(text)
        settledKeyboard()
    }

    /// Whether a keyboard key can be tapped. On iOS 27 a key can report a frame off the screen
    /// while the keyboard settles, and `isHittable` then fails the test instead of saying no.
    public func canTapKey(_ key: XCUIElement) -> Bool {
        guard key.exists, app.windows.firstMatch.frame.contains(key.frame) else { return false }
        return key.isHittable && key.isEnabled
    }

    /// The software keyboard once it is up and holds still, or nil if none comes.
    @discardableResult
    public func settledKeyboard(timeout: TimeInterval = 3) -> XCUIElement? {
        let keyboard = app.keyboards.firstMatch
        return keyboard.waitUntilSettled(timeout: timeout) ? keyboard : nil
    }

    /// Closes the software keyboard, if one is up.
    public func dismissKeyboard() {
        // A keyboard still moving on a slow machine is closed all the same.
        settledKeyboard()
        let keyboard = app.keyboards.firstMatch
        guard keyboard.exists else { return }
        for key in keyboardDismissKeys {
            let button = app.keyboards.buttons[key]
            if canTapKey(button) {
                button.tap()
                _ = keyboard.waitUntilGone(timeout: 2)
                return
            }
        }
        // On an iPad on iOS 27 no key may pass, and a tap on the bar there lands on the search
        // field and opens its edit menu. Return closes the keyboard as the search key does. A
        // keyboard on its way out has no field with focus left to take it.
        let focused = app.descendants(matching: .any)
            .matching(NSPredicate(format: "hasKeyboardFocus == true")).firstMatch
        if focused.exists {
            focused.typeText("\n")
        }
        _ = keyboard.waitUntilGone(timeout: 2)
    }
}
