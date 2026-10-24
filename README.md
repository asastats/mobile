# ASA Stats app

The iOS and Android app "ASA Stats" (`com.asastats.app`). It is a
[Capacitor 8](https://capacitorjs.com/) shell that loads the live website,
https://www.asastats.com, and adds native features around it. The website
recognises the app by the user-agent token `ASAStatsApp/<version> (<ios|android>)`.

Why it is built this way, and what each setting guards against, is in
[`docs/logbook.md`](docs/logbook.md).

## Requirements

Node 22 or newer. Native builds need JDK 21 and the Android SDK (API 36) for
Android, and Xcode 26 for iOS. Releases are built by GitHub Actions
(`.github/workflows/`), not by hand.

## Run against a local website

The app loads whatever `ASASTATS_URL` names at `cap sync`/`cap run` time:

    npm ci
    ASASTATS_URL=http://<lan-ip>:8000 npx cap run android

Run Django with `runserver 0.0.0.0:8000` so the phone can reach it. An `http:`
URL turns on cleartext traffic; a release build (`ASASTATS_RELEASE=1`, set in
CI) refuses one. Without `ASASTATS_URL` the app loads production.

Run `npx cap sync` again before committing. It writes the URL into the
committed native configs, and those must point at production.

## Builds

| Workflow | Always | With secrets |
|---|---|---|
| `android.yml` | debug APK (`com.asastats.app.debug`, "ASA Stats dev"), artifact `asastats-debug-apk` | signed `.aab`, artifact `asastats-release-aab` |
| `ios.yml` | simulator compile | archive, sign, upload to TestFlight |

Repository secrets:

| Secret | What |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | the Play upload keystore, `base64 -w0 upload.jks` |
| `ANDROID_KEYSTORE_PASSWORD` | keystore password |
| `ANDROID_KEY_ALIAS` | key alias |
| `ANDROID_KEY_PASSWORD` | key password |
| `ASC_KEY_ID` | App Store Connect API key id |
| `ASC_ISSUER_ID` | App Store Connect issuer id |
| `ASC_KEY_P8_BASE64` | the API key file, `base64 -w0 AuthKey_XXXX.p8` |

## Icons and splash

Edit `assets/icon.png` (1024², opaque) or `assets/icon-foreground.png` (the
Android adaptive foreground), then run `python3 scripts/make-icons.py`
(Pillow) and commit the native files it rewrites.

## Versions

`package.json` holds both numbers; Gradle and the iOS workflow read them from
there.

- `version`: the store version, `1.1.0`.
- `buildNumber`: one integer for both platforms (Android `versionCode`, iOS
  `CFBundleVersion`). It starts at 110000 for 1.1.0 and goes up by one for
  **every upload** to either store. The stores reject a number they have seen.
