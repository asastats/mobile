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
