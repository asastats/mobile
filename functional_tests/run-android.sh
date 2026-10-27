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

appium --allow-insecure=uiautomator2:chromedriver_autodownload > appium.log 2>&1 &
for _ in $(seq 60); do
  curl -sf http://127.0.0.1:4723/status > /dev/null && break
  sleep 1
done
python -m pytest -c pytest.ini -v -m "${1:-live}"
