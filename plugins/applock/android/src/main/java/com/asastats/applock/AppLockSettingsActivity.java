package com.asastats.applock;

import android.os.Bundle;
import android.util.TypedValue;
import android.view.MenuItem;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.SwitchCompat;
import androidx.biometric.BiometricPrompt;

/** The lock's own screen, opened by AppLock.openSettings(); each change asks first. */
public class AppLockSettingsActivity extends AppCompatActivity {

    private SwitchCompat toggle;
    private TextView note;
    private BiometricPrompt prompt;
    private final AppLockAuth.Done[] pending = new AppLockAuth.Done[1];

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTitle(R.string.applock_settings_title);
        if (getSupportActionBar() != null) getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        prompt = AppLockAuth.prompt(this, pending);

        int pad = Math.round(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 20, getResources().getDisplayMetrics()));
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(pad, pad, pad, pad);
        toggle = new SwitchCompat(this);
        toggle.setText(R.string.applock_switch);
        toggle.setTextSize(TypedValue.COMPLEX_UNIT_SP, 18);
        column.addView(toggle);
        note = new TextView(this);
        note.setPadding(0, pad, 0, 0);
        column.addView(note);
        setContentView(column);
        toggle.setOnClickListener(v -> change(toggle.isChecked()));
    }

    @Override
    protected void onResume() {
        super.onResume();
        boolean available = AppLockAuth.canAuthenticate(this);
        if (!available && AppLockAuth.enabled(this)) AppLockAuth.setEnabled(this, false);
        toggle.setEnabled(available);
        toggle.setChecked(AppLockAuth.enabled(this));
        note.setText(available ? R.string.applock_note : R.string.applock_unavailable);
    }

    /** The switch shows the saved state until the prompt succeeds. */
    private void change(boolean on) {
        toggle.setChecked(!on);
        AppLockAuth.ask(prompt, getString(on ? R.string.applock_enable_title : R.string.applock_disable_title), pending, ok -> {
            if (!ok) return;
            AppLockAuth.setEnabled(this, on);
            toggle.setChecked(on);
        });
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == android.R.id.home) {
            finish();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }
}
