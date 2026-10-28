import XCTest

@testable import AppLockPlugin

final class LockPolicyTests: XCTestCase {
    private let t: TimeInterval = 1000

    func testStartsLockedOnlyWhenOn() {
        XCTAssertTrue(LockPolicy(enabled: true).isLocked)
        XCTAssertFalse(LockPolicy(enabled: false).isLocked)
        var on = LockPolicy(enabled: true)
        XCTAssertEqual(on.foreground(now: t, canAuthenticate: true), .prompt)
        var off = LockPolicy(enabled: false)
        XCTAssertEqual(off.foreground(now: t, canAuthenticate: true), .show)
    }

    func testLocksAfterAMinuteAwayAndNotBefore() {
        var policy = unlocked()
        policy.background(now: t)
        XCTAssertEqual(policy.foreground(now: t + LockPolicy.graceSeconds - 1, canAuthenticate: true), .show)

        policy.background(now: t)
        XCTAssertEqual(policy.foreground(now: t + LockPolicy.graceSeconds, canAuthenticate: true), .prompt)
        XCTAssertTrue(policy.isLocked)
    }

    func testAResumeWithNoTimeAwayDoesNotLock() {
        var policy = unlocked()
        XCTAssertEqual(policy.foreground(now: t, canAuthenticate: true), .show)
    }

    func testStaysLockedUntilThePromptSucceeds() {
        var policy = LockPolicy(enabled: true)
        policy.authenticating()
        XCTAssertEqual(policy.foreground(now: t, canAuthenticate: true), .wait)
        policy.authenticated(false)
        XCTAssertTrue(policy.isLocked)
        XCTAssertEqual(policy.foreground(now: t, canAuthenticate: true), .prompt)

        policy.authenticating()
        policy.authenticated(true)
        XCTAssertFalse(policy.isLocked)
    }

    func testThePromptsOwnInactivityIsNotTimeAway() {
        var policy = unlocked()
        policy.authenticating()
        policy.background(now: t)
        policy.authenticated(true)
        XCTAssertEqual(policy.foreground(now: t + LockPolicy.graceSeconds, canAuthenticate: true), .show)
    }

    func testTurnsItselfOffWhenThePhoneHasNoPasscode() {
        var policy = LockPolicy(enabled: true)
        XCTAssertEqual(policy.foreground(now: t, canAuthenticate: false), .disabled)
        XCTAssertFalse(policy.isEnabled)
        XCTAssertFalse(policy.isLocked)
        XCTAssertEqual(policy.foreground(now: t, canAuthenticate: false), .show)
    }

    func testOffNeverLocks() {
        var policy = LockPolicy(enabled: false)
        policy.background(now: t)
        XCTAssertEqual(policy.foreground(now: t + 10 * LockPolicy.graceSeconds, canAuthenticate: true), .show)
    }

    func testTurningItOnDoesNotLockTheAppInUseAndOffUnlocks() {
        var policy = LockPolicy(enabled: false)
        policy.setEnabled(true)
        XCTAssertTrue(policy.isEnabled)
        XCTAssertFalse(policy.isLocked)

        var locked = LockPolicy(enabled: true)
        locked.setEnabled(false)
        XCTAssertFalse(locked.isLocked)
    }

    private func unlocked() -> LockPolicy {
        var policy = LockPolicy(enabled: true)
        policy.authenticating()
        policy.authenticated(true)
        return policy
    }
}
