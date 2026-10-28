package com.asastats.applock;

import android.content.Intent;
import android.graphics.Color;
import android.os.Build;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import androidx.activity.OnBackPressedCallback;
import androidx.biometric.BiometricPrompt;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * The lock is native: a cover over the WebView and the system prompt. Pages can only
 * {@code AppLock.openSettings()}. Design: capacitor/O2-BIOMETRIC-LOCK-DESIGN.md.
 */
@CapacitorPlugin(name = "AppLock")
public class AppLockPlugin extends Plugin {

    /** The app's splash background (capacitor.config.ts backgroundColor). */
    private static final int COVER_COLOR = Color.parseColor("#140a2e");

    private LockPolicy policy;
    private FrameLayout cover;
    private BiometricPrompt prompt;
    private final AppLockAuth.Done[] pending = new AppLockAuth.Done[1];
    private OnBackPressedCallback backWhileLocked;
    /** Our own settings screen stops this activity; that is not time away. */
    private boolean inSettings;

    @Override
    public void load() {
        policy = new LockPolicy(AppLockAuth.enabled(getContext()));
        prompt = AppLockAuth.prompt(getActivity(), pending);
        cover = buildCover();
        // Back on the cover leaves the app rather than reaching the page under it.
        backWhileLocked = new OnBackPressedCallback(false) {
            @Override
            public void handleOnBackPressed() {
                getActivity().moveTaskToBack(true);
            }
        };
        getActivity().getOnBackPressedDispatcher().addCallback(getActivity(), backWhileLocked);
        hideFromRecents(policy.isEnabled());
        if (policy.isLocked()) showCover();
    }

    @PluginMethod
    public void openSettings(PluginCall call) {
        inSettings = true;
        getActivity().startActivity(new Intent(getContext(), AppLockSettingsActivity.class));
        call.resolve();
    }

    @Override
    protected void handleOnStop() {
        if (inSettings || !policy.isEnabled()) return;
        policy.background(SystemClock.elapsedRealtime());
        showCover();
    }

    @Override
    protected void handleOnResume() {
        if (inSettings) {
            inSettings = false;
            policy.setEnabled(AppLockAuth.enabled(getContext()));
            hideFromRecents(policy.isEnabled());
        }
        switch (policy.foreground(SystemClock.elapsedRealtime(), AppLockAuth.canAuthenticate(getContext()))) {
            case PROMPT:
                showCover();
                ask();
                break;
            case DISABLED:
                AppLockAuth.setEnabled(getContext(), false);
                hideFromRecents(false);
                hideCover();
                break;
            case SHOW:
                hideCover();
                break;
            case WAIT:
                break;
        }
    }

    private void ask() {
        policy.authenticating();
        AppLockAuth.ask(prompt, getContext().getString(R.string.applock_unlock_title), pending, ok -> {
            policy.authenticated(ok);
            if (ok) hideCover();
        });
    }

    private FrameLayout buildCover() {
        FrameLayout view = new FrameLayout(getContext());
        view.setBackgroundColor(COVER_COLOR);
        view.setClickable(true);
        view.setFocusable(true);
        LinearLayout column = new LinearLayout(getContext());
        column.setOrientation(LinearLayout.VERTICAL);
        column.setGravity(Gravity.CENTER_HORIZONTAL);
        ImageView logo = new ImageView(getContext());
        logo.setImageDrawable(getContext().getApplicationInfo().loadIcon(getContext().getPackageManager()));
        int size = Math.round(96 * getContext().getResources().getDisplayMetrics().density);
        column.addView(logo, new LinearLayout.LayoutParams(size, size));
        Button unlock = new Button(getContext());
        unlock.setText(R.string.applock_unlock);
        unlock.setOnClickListener(v -> {
            if (policy.isLocked()) ask();
        });
        LinearLayout.LayoutParams below = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT
        );
        below.topMargin = size / 2;
        column.addView(unlock, below);
        view.addView(column, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER
        ));
        return view;
    }

    private void showCover() {
        backWhileLocked.setEnabled(true);
        if (cover.getParent() != null) return;
        ViewGroup content = getActivity().findViewById(android.R.id.content);
        content.addView(cover, new ViewGroup.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT
        ));
        cover.bringToFront();
    }

    private void hideCover() {
        backWhileLocked.setEnabled(false);
        if (cover.getParent() != null) ((ViewGroup) cover.getParent()).removeView(cover);
    }

    /** The Recents thumbnail, not screenshots (the user's choice: no FLAG_SECURE); Android 13+ only. */
    private void hideFromRecents(boolean hide) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) getActivity().setRecentsScreenshotEnabled(!hide);
    }
}
