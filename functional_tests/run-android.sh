#!/usr/bin/env bash
# Inside the emulator runner: start Appium, run one marker (live or local), keep Appium's log.
set -euo pipefail
cd "$(dirname "$0")"

ADB="${ANDROID_HOME:-/usr/local/lib/android/sdk}/platform-tools/adb"
# The slow emulator's launcher stalls ("isn't responding"); the dialog swallows Back.
"$ADB" shell settings put global hide_error_dialogs 1
# Chrome's first-run screen would stand in for the browser sheet.
"$ADB" shell 'echo "_ --disable-fre --no-default-browser-check --no-first-run" > /data/local/tmp/chrome-command-line'
"$ADB" shell am set-debug-app --persistent com.android.chrome
# The cached AVD keeps an older build; Appium would skip installing ours (logbook).
"$ADB" uninstall com.asastats.app.debug || true
# Store screenshots: a fixed clock, full battery and wifi, no notification icons.
if [ "${1:-live}" = screenshots ]; then
  "$ADB" shell settings put global sysui_demo_allowed 1
  demo() { "$ADB" shell am broadcast -a com.android.systemui.demo -e command "$@" > /dev/null; }
  demo enter
  demo clock -e hhmm 0941
  demo battery -e level 100 -e plugged false
  demo network -e wifi show -e level 4
  demo notifications -e visible false
  # SystemBars.hide() would otherwise show "Viewing full screen" over the first shots.
  "$ADB" shell settings put secure immersive_mode_confirmations confirmed
  # SwiftShader's GPU raster drew cyberpunk's out-of-gamut yellow as green tiles (logbook).
  "$ADB" shell 'echo "_ --disable-gpu-rasterization" > /data/local/tmp/webview-command-line'
fi

appium --allow-insecure=uiautomator2:chromedriver_autodownload,uiautomator2:adb_shell > appium.log 2>&1 &
for _ in $(seq 60); do
  curl -sf http://127.0.0.1:4723/status > /dev/null && break
  sleep 1
done
python -m pytest -c pytest.ini -v -m "${1:-live}"
