package com.asastats.applock;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import com.asastats.applock.LockPolicy.Action;
import org.junit.Test;

public class LockPolicyTest {

    private static final long T = 1_000_000L;

    @Test
    public void startsLockedOnlyWhenOn() {
        assertTrue(new LockPolicy(true).isLocked());
        assertFalse(new LockPolicy(false).isLocked());
        assertEquals(Action.PROMPT, new LockPolicy(true).foreground(T, true));
        assertEquals(Action.SHOW, new LockPolicy(false).foreground(T, true));
    }

    @Test
    public void locksAfterAMinuteAwayAndNotBefore() {
        LockPolicy policy = unlocked();
        policy.background(T);
        assertEquals(Action.SHOW, policy.foreground(T + LockPolicy.GRACE_MS - 1, true));

        policy.background(T);
        assertEquals(Action.PROMPT, policy.foreground(T + LockPolicy.GRACE_MS, true));
        assertTrue(policy.isLocked());
    }

    @Test
    public void aResumeWithNoTimeAwayDoesNotLock() {
        assertEquals(Action.SHOW, unlocked().foreground(T, true));
    }

    @Test
    public void staysLockedUntilThePromptSucceeds() {
        LockPolicy policy = new LockPolicy(true);
        policy.authenticating();
        assertEquals(Action.WAIT, policy.foreground(T, true));
        policy.authenticated(false);
        assertTrue(policy.isLocked());
        assertEquals(Action.PROMPT, policy.foreground(T, true));

        policy.authenticating();
        policy.authenticated(true);
        assertFalse(policy.isLocked());
    }

    @Test
    public void thePromptsOwnScreensAreNotTimeAway() {
        LockPolicy policy = unlocked();
        policy.authenticating();
        policy.background(T);
        policy.authenticated(true);
        assertEquals(Action.SHOW, policy.foreground(T + LockPolicy.GRACE_MS, true));
    }

    @Test
    public void turnsItselfOffWhenThePhoneHasNoScreenLock() {
        LockPolicy policy = new LockPolicy(true);
        assertEquals(Action.DISABLED, policy.foreground(T, false));
        assertFalse(policy.isEnabled());
        assertFalse(policy.isLocked());
        assertEquals(Action.SHOW, policy.foreground(T, false));
    }

    @Test
    public void offNeverLocks() {
        LockPolicy policy = new LockPolicy(false);
        policy.background(T);
        assertEquals(Action.SHOW, policy.foreground(T + 10 * LockPolicy.GRACE_MS, true));
    }

    @Test
    public void turningItOnDoesNotLockTheAppInUseAndOffUnlocks() {
        LockPolicy policy = new LockPolicy(false);
        policy.setEnabled(true);
        assertTrue(policy.isEnabled());
        assertFalse(policy.isLocked());

        LockPolicy locked = new LockPolicy(true);
        locked.setEnabled(false);
        assertFalse(locked.isLocked());
    }

    private static LockPolicy unlocked() {
        LockPolicy policy = new LockPolicy(true);
        policy.authenticating();
        policy.authenticated(true);
        return policy;
    }
}
