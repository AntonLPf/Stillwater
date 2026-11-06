import XCTest

extension NSPredicate {
    /// Matches an element by its identifier and its label together.
    public static func identifier(_ identifier: String, label: String) -> NSPredicate {
        NSPredicate(format: "identifier == %@ AND label == %@", identifier, label)
    }
}

extension XCUIElementQuery {
    public func matching(identifier: String, label: String) -> XCUIElementQuery {
        matching(NSPredicate.identifier(identifier, label: label))
    }
}
