package com.asastats.nativesignin;

import java.util.regex.Pattern;

/**
 * One native sign-in, checked before any sheet opens. Every page of the site can
 * call the plugin, so nothing from JavaScript reaches the sheet unchecked.
 */
public final class NativeSignInRequest {

    /** Rejection messages {@code signIn.ts} reads; the iOS plugin uses the same. */
    public static final String INVALID = "invalid";
    public static final String BUSY = "busy";
    public static final String CANCELLED = "cancelled";
    /** No Google account on the phone: {@code signIn.ts} falls back to the browser. */
    public static final String UNAVAILABLE = "unavailable";
    public static final String FAILED = "failed";

    /** Credential Manager's {@code GetCredentialException} types. */
    static final String TYPE_USER_CANCELED =
        "android.credentials.GetCredentialException.TYPE_USER_CANCELED";
    static final String TYPE_NO_CREDENTIAL =
        "android.credentials.GetCredentialException.TYPE_NO_CREDENTIAL";

    /** Android has no native Apple sheet. Must match frontend {@code NATIVE_PROVIDERS}. */
    public static final String GOOGLE = "google";

    /** The server's {@code secrets.token_urlsafe(32)}. */
    private static final Pattern NONCE = Pattern.compile("^[A-Za-z0-9_-]{43}$");
    private static final Pattern CLIENT_ID =
        Pattern.compile("^[0-9]+-[a-z0-9]+\\.apps\\.googleusercontent\\.com$");

    public final String nonce;
    public final String serverClientId;

    private NativeSignInRequest(String nonce, String serverClientId) {
        this.nonce = nonce;
        this.serverClientId = serverClientId;
    }

    /** @return whether this platform has a native sheet for {@code provider}. */
    public static boolean supports(String provider) {
        return GOOGLE.equals(provider);
    }

    /** @return null unless every value is well formed. */
    public static NativeSignInRequest create(String provider, String nonce, String serverClientId) {
        if (!supports(provider)) return null;
        if (nonce == null || !NONCE.matcher(nonce).matches()) return null;
        if (serverClientId == null || !CLIENT_ID.matcher(serverClientId).matches()) return null;
        return new NativeSignInRequest(nonce, serverClientId);
    }

    /** @return the rejection message for a Credential Manager failure type. */
    public static String failureFor(String type) {
        if (TYPE_USER_CANCELED.equals(type)) return CANCELLED;
        if (TYPE_NO_CREDENTIAL.equals(type)) return UNAVAILABLE;
        return FAILED;
    }
}
