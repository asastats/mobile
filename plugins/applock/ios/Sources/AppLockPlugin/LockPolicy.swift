import Foundation

/// When the app locks: on start, and back after `graceSeconds` or more away.
/// No UIKit here, so the unit tests cover it whole. Design: capacitor/O2-BIOMETRIC-LOCK-DESIGN.md.
public struct LockPolicy {

    /// Away this long or longer locks; a wallet or browser hand-off is usually shorter.
    public static let graceSeconds: TimeInterval = 60

    /// What the app does on coming to the front.
    public enum Action: Equatable {
        /// Unlocked: hide the cover.
        case show
        /// Locked: keep the cover and ask.
        case prompt
        /// A prompt is open (it makes the app inactive and active again): leave it be.
        case wait
        /// The phone has no passcode any more: the lock turned itself off. Save and show.
        case disabled
    }

    public private(set) var isEnabled: Bool
    public private(set) var isLocked: Bool
    private var isAuthenticating = false
    private var backgroundAt: TimeInterval?

    /// - Parameter enabled: the saved setting; a cold start with it on starts locked.
    public init(enabled: Bool) {
        isEnabled = enabled
        isLocked = enabled
    }

    /// The settings screen changed it; turning it on does not lock the app being used.
    public mutating func setEnabled(_ enabled: Bool) {
        isEnabled = enabled
        if !enabled { isLocked = false }
    }

    /// - Parameter now: a monotonic clock, in seconds.
    public mutating func background(now: TimeInterval) {
        if !isAuthenticating { backgroundAt = now }
    }

    /// - Parameters:
    ///   - now: the same clock as `background(now:)`.
    ///   - canAuthenticate: whether the phone still has Face ID, Touch ID or a passcode.
    public mutating func foreground(now: TimeInterval, canAuthenticate: Bool) -> Action {
        if isAuthenticating { return .wait }
        if isEnabled && !canAuthenticate {
            setEnabled(false)
            backgroundAt = nil
            return .disabled
        }
        if isEnabled, let away = backgroundAt, now - away >= LockPolicy.graceSeconds { isLocked = true }
        backgroundAt = nil
        return isLocked ? .prompt : .show
    }

    /// The prompt opened.
    public mutating func authenticating() {
        isAuthenticating = true
    }

    /// The prompt closed: unlocked if it succeeded, still locked otherwise.
    public mutating func authenticated(_ ok: Bool) {
        isAuthenticating = false
        if ok { isLocked = false }
    }
}
