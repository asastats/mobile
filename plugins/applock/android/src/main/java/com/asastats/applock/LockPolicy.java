package com.asastats.applock;

/**
 * When the app locks: on start, and back after {@link #GRACE_MS} or more away.
 * No Android here, so the unit tests cover it whole. Design: capacitor/O2-BIOMETRIC-LOCK-DESIGN.md.
 */
public final class LockPolicy {

    /** Away this long or longer locks; a wallet or browser hand-off is usually shorter. */
    public static final long GRACE_MS = 60_000L;

    /** What the app does on coming to the front. */
    public enum Action {
        /** Unlocked: hide the cover. */
        SHOW,
        /** Locked: keep the cover and ask. */
        PROMPT,
        /** A prompt is open (its own screens send the app back and forth): leave it be. */
        WAIT,
        /** The phone has no screen lock any more: the lock turned itself off. Save and show. */
        DISABLED
    }

    private boolean enabled;
    private boolean locked;
    private boolean authenticating;
    private long backgroundAt = -1;

    /** @param enabled the saved setting; a cold start with it on starts locked. */
    public LockPolicy(boolean enabled) {
        this.enabled = enabled;
        this.locked = enabled;
    }

    public boolean isEnabled() {
        return enabled;
    }

    public boolean isLocked() {
        return locked;
    }

    /** The settings screen changed it; turning it on does not lock the app being used. */
    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
        if (!enabled) locked = false;
    }

    /** @param now a monotonic clock, in ms. */
    public void background(long now) {
        if (!authenticating) backgroundAt = now;
    }

    /**
     * @param now the same clock as {@link #background}.
     * @param canAuthenticate whether the phone still has a fingerprint, face or screen lock.
     */
    public Action foreground(long now, boolean canAuthenticate) {
        if (authenticating) return Action.WAIT;
        if (enabled && !canAuthenticate) {
            setEnabled(false);
            backgroundAt = -1;
            return Action.DISABLED;
        }
        if (enabled && backgroundAt >= 0 && now - backgroundAt >= GRACE_MS) locked = true;
        backgroundAt = -1;
        return locked ? Action.PROMPT : Action.SHOW;
    }

    /** The prompt opened. */
    public void authenticating() {
        authenticating = true;
    }

    /** The prompt closed: unlocked if it succeeded, still locked otherwise. */
    public void authenticated(boolean ok) {
        authenticating = false;
        if (ok) locked = false;
    }
}
