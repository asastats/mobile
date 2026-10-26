package com.asastats.webauth;

import android.content.Intent;
import android.net.Uri;
import androidx.activity.result.ActivityResultLauncher;
import androidx.browser.auth.AuthTabIntent;
import androidx.browser.customtabs.CustomTabsClient;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * {@code WebAuth.start({provider, challenge, next})} → {@code {url}}; rejects with a
 * {@link WebAuthController} failure name. Design: capacitor/F4-DESIGN.md §9.
 */
@CapacitorPlugin(name = "WebAuth")
public class WebAuthPlugin extends Plugin {

    private ActivityResultLauncher<Intent> authTab;
    private WebAuthController controller;
    private WebAuthController.Callback pending;

    @Override
    public void load() {
        // Registered while the activity is being created, as AndroidX requires.
        authTab = AuthTabIntent.registerActivityResultLauncher(getActivity(), this::onAuthResult);
        controller = new WebAuthController(this::launch);
    }

    @PluginMethod
    public void start(PluginCall call) {
        controller.start(
            getBridge().getConfig().getServerUrl(),
            call.getString("provider"),
            call.getString("challenge"),
            call.getString("next"),
            (url, failure) -> {
                if (failure != null) {
                    call.reject(failure);
                    return;
                }
                JSObject result = new JSObject();
                result.put("url", url);
                call.resolve(result);
            }
        );
    }

    /** Auth Tab with an https redirect, which Chrome verifies against assetlinks.json. */
    private boolean launch(String url, String host, String path, WebAuthController.Callback callback) {
        String browser = CustomTabsClient.getPackageName(getContext(), null);
        if (browser == null || !CustomTabsClient.isAuthTabSupported(getContext(), browser)) {
            return false;
        }
        pending = callback;
        AuthTabIntent intent = new AuthTabIntent.Builder().build();
        intent.intent.setPackage(browser);
        intent.launch(authTab, Uri.parse(url), host, path);
        return true;
    }

    private void onAuthResult(AuthTabIntent.AuthResult result) {
        WebAuthController.Callback callback = pending;
        pending = null;
        if (callback == null) return;
        if (result.resultCode == AuthTabIntent.RESULT_OK && result.resultUri != null) {
            callback.done(result.resultUri.toString(), null);
        } else if (result.resultCode == AuthTabIntent.RESULT_CANCELED) {
            callback.done(null, WebAuthController.CANCELLED);
        } else {
            callback.done(null, WebAuthController.FAILED);
        }
    }
}
