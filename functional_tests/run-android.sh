#!/usr/bin/env bash
# Inside the emulator runner: start Appium, run one marker (live or local), keep Appium's log.
set -euo pipefail
cd "$(dirname "$0")"

appium --allow-insecure=uiautomator2:chromedriver_autodownload > appium.log 2>&1 &
for _ in $(seq 60); do
  curl -sf http://127.0.0.1:4723/status > /dev/null && break
  sleep 1
done
python -m pytest -c pytest.ini -v -m "${1:-live}"
