#!/usr/bin/env bash
# Before the emulator boots: an exact portrait screen, WIDTH HEIGHT DENSITY. No arguments: the profile's own.
set -euo pipefail
[ $# -eq 3 ] || exit 0

# android-emulator-runner's default avd-name is "test".
CONFIG="$HOME/.android/avd/test.avd/config.ini"
sed -i '/^hw\.lcd\.\(width\|height\|density\)=/d; /^hw\.initialOrientation=/d; /^skin\./d' "$CONFIG"
printf '%s\n' "hw.lcd.width=$1" "hw.lcd.height=$2" "hw.lcd.density=$3" \
  "hw.initialOrientation=portrait" "skin.name=$1x$2" "skin.path=_no_skin" >> "$CONFIG"
grep -E '^(hw\.lcd|hw\.initialOrientation|skin)' "$CONFIG"
