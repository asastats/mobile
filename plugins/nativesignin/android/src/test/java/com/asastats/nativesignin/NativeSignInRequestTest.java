package com.asastats.nativesignin;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class NativeSignInRequestTest {

    private static final String NONCE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJ0123-_6";
    private static final String CLIENT =
        "1054116980925-bje7a3i2vbttilei8re269n9q4lu42kk.apps.googleusercontent.com";

    @Test
    public void onlyGoogleHasANativeSheet() {
        assertTrue(NativeSignInRequest.supports("google"));
        assertFalse(NativeSignInRequest.supports("apple"));
        assertFalse(NativeSignInRequest.supports(null));
    }

    @Test
    public void wellFormedRequestKeepsItsValues() {
        NativeSignInRequest request = NativeSignInRequest.create("google", NONCE, CLIENT);
        assertEquals(NONCE, request.nonce);
        assertEquals(CLIENT, request.serverClientId);
    }

    @Test
    public void refusesAnUnsupportedProvider() {
        assertNull(NativeSignInRequest.create("apple", NONCE, CLIENT));
    }

    @Test
    public void refusesABadNonce() {
        assertNull(NativeSignInRequest.create("google", null, CLIENT));
        assertNull(NativeSignInRequest.create("google", "short", CLIENT));
        assertNull(NativeSignInRequest.create("google", NONCE.replace('a', '='), CLIENT));
    }

    @Test
    public void refusesABadClientId() {
        assertNull(NativeSignInRequest.create("google", NONCE, null));
        assertNull(NativeSignInRequest.create("google", NONCE, "evil.example.com"));
        assertNull(NativeSignInRequest.create("google", NONCE, CLIENT + ".evil.com"));
    }

    @Test
    public void mapsCredentialManagerFailures() {
        assertEquals("cancelled", NativeSignInRequest.failureFor(
            "android.credentials.GetCredentialException.TYPE_USER_CANCELED"));
        assertEquals("unavailable", NativeSignInRequest.failureFor(
            "android.credentials.GetCredentialException.TYPE_NO_CREDENTIAL"));
        assertEquals("failed", NativeSignInRequest.failureFor("anything else"));
        assertEquals("failed", NativeSignInRequest.failureFor(null));
    }
}
