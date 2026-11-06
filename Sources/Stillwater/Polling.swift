import Foundation

/// Checks `condition` at once and then every tenth of a second, until it holds or `timeout`
/// passes. Returns whether it held.
@MainActor
func poll(_ timeout: TimeInterval, interval: TimeInterval = 0.1, until condition: () -> Bool) -> Bool {
    let deadline = Date().addingTimeInterval(timeout)
    while !condition() {
        guard Date() < deadline else { return false }
        Thread.sleep(forTimeInterval: interval)
    }
    return true
}
