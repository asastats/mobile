# Mobile app logbook

Why the code in this repository is the way it is: the measurements, the
outages, the decisions taken and the ones reversed.

One section per file or directory, under its path from the repository root.
Inside it, `## Module` holds notes about the file as a whole and a subsection
per setting or function carries the rest.

The code carries what a reader needs to *use* it correctly. This carries what
they would need to *change* it safely. Nothing here is required reading to work
in a file; it is here so that nobody has to reconstruct a decision from a diff,
and so that the decision survives the comment being edited away.

Entries are dated where the date is known, and append-only: a note that turned
out to be wrong gets a correction beneath it rather than an edit, because "we
believed X until 2026-09-19" is the useful part.

The plan this repository implements, and the research behind it, live in the
workspace's `capacitor/HANDOFF.md` and `capacitor/RESEARCH.md`.

---

## Repository

### Why a shell around the live site (2026-10-24)

The website is server-rendered Django + htmx, and its widgets are server-side
too. Bundling it into the app would fork every page. Loading
`https://www.asastats.com` with `server.url` keeps one codebase, and the app
stays at parity with the site automatically. Capacitor's docs call `server.url`
"not intended for production". What that costs: the app needs the network to
start (covered by `errorPath`), and Apple 4.2 ("repackaged website") is a
review risk, answered by native features.

Rejected: a bundled shell that navigates to the site through `allowNavigation`.
On Android the bridge is injected only for the app's own origin, so pages reached
that way have no plugins (Capacitor #8661, fix deferred to Capacitor 10).

### Plugins are the attack surface

Every page on www.asastats.com can call every registered plugin. Register only
what the plan lists. Never add an HTTP plugin (`CapacitorHttp` stays off) or
broad filesystem access. Revisit this before any third-party widget is admitted.

### `npm audit` (2026-10-24)

Three moderate findings: `uuid` < 11.1.1, pulled in by `xcode`, pulled in by
`@capacitor/cli`. That is CLI-only code that edits Xcode projects on the
developer's machine; none of it ships in the app. `npm audit fix --force` would
downgrade the CLI to 8.4.3, out of step with the 8.5.3 runtime, so it was not
applied. Re-check on the next Capacitor upgrade.

### TypeScript is pinned to 5 (2026-10-24)

`npm install typescript` gave 7.0, the native port. The Capacitor CLI reads
`capacitor.config.ts` with `require('typescript')` and its compiler API
(`@capacitor/cli/dist/config.js`). In 7.0 the package's main entry is only
`lib/version.cjs`; the API moved under `typescript/unstable/*`. Move to 7 when
the Capacitor CLI supports it.

---

## capacitor.config.ts

### `server.url` and `ASASTATS_URL`

The URL is read at `cap sync`/`cap run` time and copied into the native
`capacitor.config.json` files. A non-https URL is allowed only for development
against `runserver` on the LAN, and it turns on `cleartext`. `ASASTATS_RELEASE`
(set by both CI workflows) makes the config throw on one, so a LAN address
cannot reach a store build.

### `www/server-url.js` is written by the config (2026-10-24)

`offline.html` needs the server URL for its Retry button. Android serves the
`errorPath` page at `<server origin>/offline.html`, so `location.origin` would
do there. iOS loads it from `capacitor://localhost/offline.html`
(`CAPInstanceConfiguration.errorPathURL`), and its `window.WEBVIEW_SERVER_URL`
is that local URL, not the server's. The config is the one place that knows the
URL and it runs before every sync, so it writes the file there. The file is
git-ignored.

### `server.errorPath` on Android fires on HTTP errors too (2026-10-24)

`BridgeWebViewClient.onReceivedHttpError` loads the error page for **any**
main-frame HTTP error, not only network failures. A 404 bundle name, a 403 or a
500 on the site would show "No connection". iOS only falls back on navigation
failures (`didFail`, `didFailProvisionalNavigation`). Spike check S11 measures
it. The likely fix is a `WebViewListener`, or a `BridgeWebViewClient` subclass
in `MainActivity` that skips the error page for HTTP status errors.

### User-agent token

`ASAStatsApp/<version> (<ios|android>)`, with the version taken from
`package.json`. `frontend/website/core/appclient.py` parses it with one regex;
change both together.

### `backgroundColor`

`#140a2e` is the icon's background colour, so the launch and the first paint
blend with the icon.

---

## android/app/build.gradle

### Versions from `package.json`

`versionName` = `version`, `versionCode` = `buildNumber`. iOS uses the same two
numbers (the iOS workflow passes them to `xcodebuild`), so one integer goes up
for every upload to either store. The Flutter app's last build on both stores
was 38. 1.1.0 starts at 110000, which leaves room above it and reads as the
version (`1.1.0` → `110000`).

### Debug builds are `com.asastats.app.debug` (2026-10-24)

The Flutter app on the user's phone is `com.asastats.app`, signed with the store
key. A CI debug APK under the same id fails to install over it ("package
conflicts"), and uninstalling the store app to test would lose its data. With
the suffix, the spike installs beside it. The custom URL scheme stays
`com.asastats.app`. App Links never verify for the debug id, which is expected.

### Release signing from environment variables

The upload keystore is decoded from a repository secret into the runner's temp
directory. Without `ANDROID_KEYSTORE_FILE`, a release build comes out unsigned
rather than failing. That keeps `bundleRelease` usable before the keystore
arrives (decision D1).

---

## android/app/src/main/AndroidManifest.xml

### `allowBackup="false"` (2026-10-24)

Android auto-backup would copy the WebView's data directory, including the
site's session cookie, to the user's Google backup and restore it on another
device. The app keeps nothing else worth backing up: everything lives on the
server.

### App Links paths (2026-10-24)

The site's pages are mostly single root-level segments: addresses (58
characters), bundles (40), bundle names, `.algo` names. Android's
`pathPattern` has no character classes, so it cannot say "one segment" or
"everything except `/accounts/`". `pathAdvancedPattern="/[^/]+"` can, but only
on API 31+; older versions ignore it, and those links open in the browser.
Explicit prefixes (`/home/`, `/profile/`, `/widgets/`, `/export/`) work on all
versions.

`/accounts/`, `/api/`, `/app/auth/` and `/static/` must never match. If an
OAuth callback under `/accounts/` were an App Link, the system could hand it
from the sign-in Custom Tab to the app mid-flow (F4).

Known over-match: `/[^/]+` also covers root files such as `/robots.txt`,
`/sitemap.xml` and `/logo.png`. They are not linked from anywhere a user taps.
Two-segment name pages (`/<name>.algo/nfd`, `/ans`) are not covered.

Nothing verifies until the site serves `/.well-known/assetlinks.json` (F9).

### `<queries>`

Since API 30 an app sees only the packages it declares. The wallet schemes let
the OS resolve Pera/Defly/WalletConnect hand-offs. The `https` VIEW intent and
`CustomTabsService` let `@capacitor/browser` and the sign-in Custom Tab find a
browser.

---

## ios/App

### Entitlements (2026-10-24)

`App/App.entitlements` declares push (`aps-environment`, `development`; export
for App Store distribution rewrites it to `production`) and Associated Domains
for `www.asastats.com`. Signing fails until the App ID has both capabilities
turned on (user action U2). Sign in with Apple is not an entitlement here: it
runs as a web flow (F5).

### Signing in CI

Automatic signing with an App Store Connect API key (`-allowProvisioningUpdates`
plus `-authenticationKey*`). Xcode uses cloud-managed certificates, so no `.p12`
or provisioning profile is kept in secrets. The API key needs the Admin role
for that. If cloud signing is refused, the fallback is a distribution `.p12`
and profile imported into a temporary keychain.

The export uploads straight to App Store Connect (`destination: upload`), so no
`.ipa` is kept as an artifact.

### `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION`

The project file holds 1.1.0 / 110000 for local builds; CI overrides both from
`package.json`. Keep them in step when bumping by hand.

---

## scripts/make-icons.py, assets/ (2026-10-24)

### Why a Pillow script and not `@capacitor/assets`

`@capacitor/assets` renders with `sharp` 0.32, whose install script downloads
a prebuilt libvips. npm 11 blocks install scripts until they are approved one
by one, so the tool installed but could not render. The native projects
already hold every icon and splash file at its final path and size (from
`cap add`), so the script only overwrites them. Approving a native-binary
download to resize a few PNGs was not worth it. Running it again is
idempotent: it reads each target's size from the file it replaces.

### Sources and what is derived from them

- `assets/icon.png`: the user's 1024² icon (two-line wordmark on `#140a2e`).
  It is RGBA, though fully opaque, and App Store Connect rejects an icon with
  an alpha channel, so it is flattened to RGB for iOS
  (`AppIcon-512@2x.png`) and for the Android legacy square icon.
- `assets/icon-foreground.png`: the user's 3500² transparent wordmark, the
  Android adaptive foreground (108 dp canvas). The adaptive background is the
  colour `ic_launcher_background` = `#140A2E`.
- `ic_launcher_round.png` (Android 7.x only; 8+ uses the adaptive icon): the
  adaptive icon's visible 72 dp centre in a circle.
- Splash: the wordmark centred on `#140a2e`. The Android drawables
  (pre-12 window background) use a third of the short side. The iOS 2732²
  image is aspect-filled to the screen height by `LaunchScreen.storyboard`,
  about twice the size on a phone, so it uses a sixth: 36 % of an iPhone's
  width. Android 12+ ignores the drawable and draws the launcher icon on
  `windowSplashScreenBackground` (set to the same colour in `styles.xml`;
  the default is white or black).

### The adaptive foreground runs past the safe zone (measured 2026-10-24)

The farthest opaque pixel of the wordmark is at 106.5 % of the 66 dp
safe-zone radius (1139 px of 1069 px on the 3500² canvas). 1.9 % of its opaque
pixels lie outside that circle. It does fit a plain circle mask (97.6 % of the
36 dp radius). On a circle launcher the ends of "STATS" touch the edge; the
squircle is clear. The handoff had estimated about 99 %. Reported to the user as
their design decision; not changed.

The Capacitor template's leftovers `drawable-v24/ic_launcher_foreground.xml`
and `drawable/ic_launcher_background.xml` (the Android robot) were
referenced by nothing once the adaptive icon pointed at the mipmaps, so they
were deleted.

---

## package.json — plugins (A5, 2026-10-24)

Registered: App, Browser, Share, SplashScreen, StatusBar, Filesystem,
Preferences, Haptics. Every page on www.asastats.com can call all of them (see
"Plugins are the attack surface" above). On Android, Filesystem brings no
storage permission, so pages reach only the app's own directories. Haptics
adds `VIBRATE`.

`@capacitor-firebase/messaging` is **not** added yet. Without
`GoogleService-Info.plist` (user action U5), calling `FirebaseApp.configure()`
crashes the iOS app at launch, and nothing calls push before F8. It comes with
F8, together with the config files.

## capacitor.config.ts — `SplashScreen` auto-hides after 3 s (2026-10-24)

The handoff planned `launchAutoHide: false`, with app.js hiding the splash and
"a timeout in the shell" as the fallback. The plugin has no fallback timeout
when auto-hide is off: if app.js never runs (offline page, an old website
deploy, a JavaScript error), the splash would stay up for good. So auto-hide
stays on with a 3-second ceiling, and app.js calls `SplashScreen.hide()` as
soon as the page is ready. Until the website ships F3, every launch shows the
splash for the full 3 s.

## android/app/src/main/res/xml/file_paths.xml — cache only (2026-10-24)

The Capacitor template also exposed `<external-path path=".">`: the whole
external storage root could be handed out through the `FileProvider`. Every
page of the site can call Share, so the provider exposes only what the
download flow uses. The website's `app.js` writes downloads to the cache
directory (`Directory.Cache`) and shares them from there. If a later feature
writes elsewhere, add that directory here, nothing wider.

**Correction 2026-10-24** to "The adaptive foreground runs past the safe
zone" above: the user delivered a new `asastats-foreground.png` the same day,
with the wordmark scaled down. Its farthest opaque pixel is now at 93.1 % of
the 66 dp safe-zone radius, with no pixel outside, so every launcher mask
shows it whole. Icons regenerated with `scripts/make-icons.py`.

**Correction 2026-10-25** to "package.json — plugins (A5)" above: with
`@capacitor-firebase/messaging` 8.5.2 a missing `GoogleService-Info.plist` no
longer crashes the app. The plugin checks `FirebaseOptions.defaultOptions()`
first and only logs "Firebase was not configured" (`ios/Plugin/FirebaseMessaging.swift`).
The build still needs the file, because the project now lists it as a resource
(next entry).

## package.json, capacitor.config.ts, ios/App, .github/workflows — native push (F8, 2026-10-25)

- **`@capacitor-firebase/messaging` pinned at 8.5.2.** Its `firebase` peer is
  optional (`peerDependenciesMeta`), so npm does not install the Firebase web
  SDK; nothing here needs it. The website's `app.js` reaches the plugin with
  `registerPlugin("FirebaseMessaging")` instead of importing this package
  (frontend `docs/logbook.md`, F8), so the version is pinned only here; if its
  API changes, update the declarations in frontend `wallet/src/app/push.ts`.
  Every page can call it (see "Plugins are the attack surface"): the worst a
  page can do is ask for notification permission or read this phone's FCM
  token, which only lets it send to this phone through our own Firebase
  project.
- **iOS, SPM.** `experimental.ios.spm.packageOptions` with `symlink: true`, as
  the plugin's README asks, avoids a SwiftPM package identity collision
  between the npm package and the Firebase iOS SDK. `cap sync` then writes
  `ios/App/CapApp-SPM/symlinks/` with an absolute link into `node_modules`,
  so that folder is git-ignored and CI recreates it.
- **`AppDelegate.swift`** forwards the APNs token, its failure and background
  notifications to the plugin, as its README requires. `FirebaseApp.configure()`
  is called by the plugin itself, so it is not in the delegate.
- **`GoogleService-Info.plist` is a resource of the App target**
  (`project.pbxproj`, ids `A1F8C0DE2F0E0001000000{01,02}`), because Firebase
  reads it from the bundle. That makes it required at build time: the iOS
  workflow fails early, with a message, when `GOOGLE_SERVICE_INFO_PLIST_BASE64`
  is missing. The Android one stays optional: `app/build.gradle` applies
  google-services only when the JSON exists, so the spike APK still builds.
- **Both files are git-ignored** and written by CI. They are not secret (the
  app ships them), but they are tied to one Firebase project, and keeping them
  out of the repository keeps a fork from sending through ours.
- `aps-environment` stays `development` in `App.entitlements`; Xcode writes
  `production` when it exports for the App Store with the distribution
  profile. Background mode `remote-notification` was already in Info.plist
  (A3).
- **`presentationOptions: ['alert', 'badge', 'sound']`** (iOS): an alert that
  arrives while the app is open still shows as a banner. Android shows it
  through FCM's default channel.
- **Not done: an Android notification icon.** Without
  `com.google.firebase.messaging.default_notification_icon` Android draws the
  launcher icon as a white silhouette in the status bar, which for an opaque
  icon is a plain white circle or square. It needs a white-on-transparent small
  icon, which is a design choice for the user.

**Correction 2026-10-25** to "Not done: an Android notification icon" in the
F8 entry above: done, next entry.

## scripts/make-notification-icon.py, res/drawable/ic_stat_asastats.xml, AndroidManifest.xml — notification icon (2026-10-25)

- Android draws the status-bar icon from its alpha channel only, all in white.
  The launcher icon is opaque, so without
  `com.google.firebase.messaging.default_notification_icon` FCM notifications
  showed a plain white circle.
- **Shape: the full two-line wordmark, the user's choice.** Four candidates
  were rendered at 24-96 px (full wordmark, "ASA", "STATS", a single "A"). The
  single "A" was the most legible at status-bar size; the user chose the full
  wordmark. At 20 dp it is about 7.5 dp tall, so the letters are small; if
  that reads badly on real phones, the script makes switching cheap.
- **A vector drawable, not PNGs per density.** One file, sharp at every
  density, and generated from `assets/logo.svg` (a copy of the planning repo's
  `capacitor/asastats-logo.svg`) rather than drawn by hand. The script drops
  the black background, keeps both coloured groups with their transforms
  (uniform scale + translate, mapped to `<group>` attributes, which compose
  the same way), paints every shape white and centres the glyph in the
  central 20 of 24 dp. It understands only the straight-line path commands
  this logo uses and stops with an error on any other, rather than computing
  a wrong bounding box.
- Checked by translating the drawable back into SVG and rendering it: same
  silhouette, counters intact, centred. Not yet seen on a device.
- Tint `#6E2CF4` (`notification_accent`, the logo's purple), the user's
  choice. It colours the icon and app name in the expanded notification on
  Android versions that apply the notification colour.

## android/app/build.gradle — the debug build needs its own Firebase app (2026-10-25)

The first CI run with `GOOGLE_SERVICES_JSON_BASE64` failed in
`:app:processDebugGoogleServices`: "No matching client found for package name
'com.asastats.app.debug'". The google-services plugin looks up the variant's
final application id in `google-services.json`, and the debug build carries
the `.debug` suffix (see "Debug builds are `com.asastats.app.debug`" above).
The suffix stays. The debug package is registered as a second Android app in
the same Firebase project, so one `google-services.json` lists both, and the
debug APK used for testing receives push too. Release builds are unaffected.
The steps are USER-ACTIONS U5 step 7 in the planning repo.

## package.json — no third-party plugin for the WebAuth sheet (A6, 2026-10-26)

HANDOFF A6 asked to look for a maintained Capacitor 8 plugin with SPM
support that opens ASWebAuthenticationSession / Custom Tabs and returns the
callback URL, before writing a local `WebAuth` plugin. None fits:

- `@capgo/inappbrowser` has `openSecureWindow` (Capacitor 8, `Package.swift`),
  but registering it also hands every page of www.asastats.com
  `executeScript`, `getCookies`, request proxying and camera/microphone grants.
  The shell loads the live site, so any plugin's whole surface is the site's
  (HANDOFF §3). Rejected.
- `@capgo/capacitor-social-login`: native provider SDKs, and its generic OAuth
  mode on Android runs in an embedded WebView (their issue #442), which Google
  refuses. Rejected.
- `@capacitor/browser` and the official InAppBrowser open SFSafariViewController
  / a Custom Tab with no callback. Not enough.

So the plugin is local, one method, as planned. Android uses
`androidx.browser` 1.9's Auth Tab (`AuthTabIntent`, Chrome 137+), which
returns the redirect to the launching activity, and falls back to a plain
Custom Tab plus the `com.asastats.app` intent filter when
`isAuthTabSupported()` is false. Design: `capacitor/F4-DESIGN.md`, awaiting
the user's approval; nothing is built yet.

## plugins/webauth/, package.json, ios/App/App/App.entitlements, .github/workflows — the WebAuth plugin (F4, 2026-10-26)

The system-browser sign-in sheet for F4. Server half and the threat model:
frontend `core/views_appauth.py` and its logbook; design and the user's answers:
`capacitor/F4-DESIGN.md` §9.

- **A local npm package (`file:plugins/webauth`), not code in the app
  target.** `npx cap sync` then wires it like any plugin: a gradle module on
  Android, a Swift package in `CapApp-SPM` on iOS, and registration in
  both generated plugin lists. Code inside `ios/App/App/` would have needed
  hand edits to `project.pbxproj` and a bridge view controller subclass.
- **Java, not Kotlin**: `MainActivity` is Java, and Kotlin would add a gradle
  plugin for ~150 lines.
- **Nothing from JavaScript reaches a URL unchecked.** Every page of
  www.asastats.com can call the plugin (HANDOFF §3), so it takes only
  `provider`, `challenge` and `next`; it builds the start URL from the
  configured `server.url`, refuses unknown providers and malformed
  challenges, and keeps the callback host and path to itself. One sign-in at
  a time.
- **https callback only** (user's answer Q5 = a): iOS 17.4+
  `ASWebAuthenticationSession` with `.https(host:path:)`, which needs the
  `webcredentials:` entitlement added here and the AASA `webcredentials`
  entry the frontend serves; Android Chrome 137+ Auth Tab with an https
  redirect, verified against `assetlinks.json`. Older systems get
  `unsupported` and `signIn.ts` says so; there is no custom-scheme fallback.
- **iOS uses an ephemeral session**, Android's Auth Tab cannot, which is why
  the server's `start` logs Chrome's session out.
- **Debug builds cannot complete it**: `com.asastats.app.debug` and a dev
  `server.url` are in no AASA or asset links document. Test F4 on the
  TestFlight / Play internal builds.
- **Tests**: the logic (`WebAuthRequest`, `WebAuthController`) is plain code
  behind a fake session/launcher. XCTest and JUnit, 100 % gates in CI
  (`jacocoCoverageCheck`, and an `xccov` check on `WebAuthRequest.swift`).
  The Capacitor and OS glue (`WebAuthPlugin`, `SystemAuthSession`) can only
  run on a device: the Appium suite in `capacitor/MOBILE-TESTING.md`.
  JUnit was run locally on 2026-10-26 without the Android SDK (14 passed,
  100 % lines and branches with JaCoCo 0.8.12); nothing native was built.
- Assumed until the first CI run: the auto-generated `AsastatsWebauth`
  scheme runs the package's tests; the Auth Tab's verification reads the
  `handle_all_urls` relation.

### Correction, 2026-10-26: the start URL can no longer fail to build

The first iOS CI run measured `WebAuthRequest.swift` at 98.7 % (75 of 76
lines): the `else { return nil }` after `URL(string:)` was never reached,
because with checked parts that URL cannot fail to parse. With one exception:
`URL.host` returns an IPv6 address without its brackets, and
`https://::1/...` does not parse. Both platforms now accept only DNS names and
IPv4 addresses as the server host (tested), and iOS builds the URL with `!`,
since nothing that passes the checks can fail. Production is
`www.asastats.com`; a LAN build uses an IPv4 address.

## jest.config.cjs, tests/, pytest.ini, requirements-dev.txt, www/offline.js, .github/workflows/tests.yml — unit tests for the shell (2026-10-26)

Step 1 of `capacitor/MOBILE-TESTING.md`, approved by the user. The rule for
every ASA Stats repository is 100 % unit coverage; until now this one had none
of its own (the website's `app.js` is tested in `frontend/wallet`).

- **Jest** covers `capacitor.config.ts` (loaded afresh per case with
  `jest.isolateModules`, `node:fs` mocked so `www/server-url.js` is not
  rewritten) and the offline page. Its Retry script moved from inline to
  `www/offline.js` so Jest can load it; a test reads `offline.html` and checks
  that it loads `server-url.js` then `offline.js` and nothing inline. No
  `tsconfig.json`: ts-jest gets its options in `jest.config.cjs`, so the
  Capacitor CLI's own reading of `capacitor.config.ts` is untouched.
- **pytest** covers both icon scripts against temporary trees (the module
  paths are monkeypatched), so a test run never rewrites the committed icons.
  `-p no:django`: the shared backend venv carries pytest-django, which would
  look for a Django project here.
- **Not unit-tested, on purpose:** `AppDelegate.swift`, `SceneDelegate.swift`
  and `MainActivity.java` are Capacitor's template plus three lines forwarding
  push callbacks. A unit test needs an XCTest target added to
  `project.pbxproj`, which cannot be built or checked without a Mac; the
  Appium suite exercises them on a device (push registration, a tapped
  notification). Raised with the user on 2026-10-26.

## functional_tests/, .github/workflows/functional.yml — Appium on an Android emulator (2026-10-26)

Step 3 of `capacitor/MOBILE-TESTING.md`, first part. Appium 3.8.0 with the
UiAutomator2 driver 8.7.0 and Appium-Python-Client 6.0.9, pytest, on an
API 34 `google_apis` x86_64 emulator (`reactivecircus/android-emulator-runner`,
KVM enabled). The debug APK loads the **live site**, so these tests are
read-only and need no account: app mode and the user-agent token,
`window.ASAStatsApp`, an external link leaving for the browser and Back
returning, the Android back button walking history, a deep link opening the
page, and offline → `offline.html` → Retry.

- **The WebView is reached through chromedriver**, which must match the
  emulator's WebView version; Appium downloads it
  (`--allow-insecure=uiautomator2:chromedriver_autodownload`, Appium 3's
  driver-scoped spelling). Capacitor debug builds allow WebView debugging,
  which this needs; a release build would not.
- **Not here yet:** anything needing an account (push permission and the
  alerts modal, downloads to the share sheet, F4 with a provider stand-in)
  needs a test server with known users. That is the functional run against a
  Django server started in CI, still to build. iOS (XCUITest driver on a
  simulator) follows once the iOS build signs.
- Its own `pytest.ini`: the root one measures `scripts/` coverage and would
  fail this run at 0 %.
- Not run locally (no emulator on the Raspberry Pi); the client API and test
  collection were checked in a throwaway venv on 2026-10-26.

## functional_tests/test_local.py, functional_tests/server/, functional.yml job `local` — Appium against a CI Django server (2026-10-26)

Step 3b of `capacitor/MOBILE-TESTING.md`. Features behind an account cannot
be tested against production without a production test account, so the
`local` job checks out `asastats/frontend` (public, with its submodules) at
`main`, runs it as frontend's own `build.yml` does (Postgres 15 and Redis
services, the same `.env` lines), seeds one verified account, and starts
`runserver` on `0.0.0.0:8000`. The APK is built with
`ASASTATS_URL=http://10.0.2.2:8000`, the emulator's name for the runner;
Capacitor's sync then allows cleartext. `functional_tests/server/app_settings.py`
is frontend's development settings plus that host, so frontend itself needs
no CI-only setting. Development settings send engine calls to
`127.0.0.1:8001`, where nothing listens: the pages tested do not need the
engine, and nothing reaches production.

What it covers: email sign-in in the WebView; the Delete account page with
its captcha; the connections page sending Google to the website (F4 Q3); a
social button going through the bridge into the WebAuth plugin and back
(over http the plugin answers `invalid`, and the native dialog says the
sign-in did not finish); and, when the Firebase config secret exists, push
registration storing an `android` device and the logout link removing it
(checked in the database).

Still not automated: a real provider sign-in (needs https and a verified
host, so a store build), downloads to the share sheet (the export endpoints
need the engine), a notification arriving.

The live and local runs share `functional_tests/` and differ by pytest marker
(`run-android.sh live|local`), because the server URL is baked into the APK.

### 2026-10-26: the first emulator run timed out booting

The first `Functional (Android)` run (live job, before 3b) failed with
"Timeout waiting for emulator to boot" on a cold API 34 `google_apis` image.
Both jobs now follow the runner's README: a cached AVD (`actions/cache`,
key `avd-34-google_apis-x86_64`) whose boot snapshot is made once, then
reused with `-no-snapshot-save`; `emulator-boot-timeout: 900`, 4 GB RAM,
4 cores, no window, audio, boot animation or back camera. If it still times
out, the next lever is an older image (API 31 boots faster); the push test
needs `google_apis` either way.

## .github/workflows/ios.yml — the coverage step names the uncovered lines (2026-10-26)

The second iOS run still failed the 100 % gate on `WebAuthRequest.swift`
after the IPv6 change, and the log carried only a percentage, so the missing
line had to be guessed from source (the guess fixed one line and not the
other). On failure the step now prints `xccov view --archive --file` for the
file: every line with its execution count.

### 2026-10-26: the last uncovered piece was a region, not a line

With the uncovered lines printed, no line had a count of 0: line coverage
was 79 of 80 because `xccov` counts a line with an unexecuted *region* as not
covered. The region was `?? ""` in `encoded`, the fallback for
`addingPercentEncoding` returning nil, which only malformed UTF-16 can cause
and a Swift `String` cannot be. `encoded` now percent-encodes the UTF-8 bytes
itself, the same algorithm as the Android `WebAuthRequest.encoded`, so there
is no optional left; a test pins `/aé b` → `/a%C3%A9%20b` on both platforms.
When the gate fails again, read the bracketed `(column, count, length)`
regions under each line, not only the line counts.
