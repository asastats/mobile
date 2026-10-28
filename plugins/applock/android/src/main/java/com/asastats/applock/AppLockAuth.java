package com.asastats.applock;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.biometric.BiometricManager;
import androidx.biometric.BiometricPrompt;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.FragmentActivity;

/** The saved setting and the system prompt, shared by the plugin and the settings screen. */
final class AppLockAuth {

    /** WEAK, not STRONG: STRONG | DEVICE_CREDENTIAL is unsupported before Android 11, and no key is unlocked. */
    static final int AUTHENTICATORS =
        BiometricManager.Authenticators.BIOMETRIC_WEAK | BiometricManager.Authenticators.DEVICE_CREDENTIAL;

    private static final String PREFS = "asastats_applock";
    private static final String ENABLED = "enabled";

    interface Done {
        void done(boolean ok);
    }

    private AppLockAuth() {}

    static boolean enabled(Context context) {
        return prefs(context).getBoolean(ENABLED, false);
    }

    static void setEnabled(Context context, boolean enabled) {
        prefs(context).edit().putBoolean(ENABLED, enabled).apply();
    }

    static boolean canAuthenticate(Context context) {
        return BiometricManager.from(context).canAuthenticate(AUTHENTICATORS) == BiometricManager.BIOMETRIC_SUCCESS;
    }

    /** Made while the activity is created, as BiometricPrompt requires; `done` gets each attempt's result. */
    static BiometricPrompt prompt(FragmentActivity activity, Done[] done) {
        return new BiometricPrompt(
            activity,
            ContextCompat.getMainExecutor(activity),
            new BiometricPrompt.AuthenticationCallback() {
                @Override
                public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result) {
                    finish(done, true);
                }

                @Override
                public void onAuthenticationError(int errorCode, CharSequence errString) {
                    finish(done, false);
                }
                // onAuthenticationFailed: a finger not recognised; the prompt stays open.
            }
        );
    }

    static void ask(BiometricPrompt prompt, String title, Done[] slot, Done done) {
        slot[0] = done;
        prompt.authenticate(
            new BiometricPrompt.PromptInfo.Builder().setTitle(title).setAllowedAuthenticators(AUTHENTICATORS).build()
        );
    }

    private static void finish(Done[] slot, boolean ok) {
        Done done = slot[0];
        slot[0] = null;
        if (done != null) done.done(ok);
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
