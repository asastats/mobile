// App Links on Android 11 and older: only `path`, `pathPrefix` and `pathPattern`
// apply there (`pathAdvancedPattern` is API 31+). See docs/logbook.md.
import * as fs from "fs";
import * as path from "path";

const MANIFEST = fs.readFileSync(
  path.resolve(__dirname, "../android/app/src/main/AndroidManifest.xml"),
  "utf8",
);

// The App Links filter: the one with android:autoVerify.
const FILTER = MANIFEST.split("<intent-filter").find((block) =>
  block.includes('android:autoVerify="true"'),
) as string;

const values = (attribute: string): string[] =>
  [...FILTER.matchAll(new RegExp(`android:${attribute}="([^"]*)"`, "g"))].map(
    // XML reading turns "\\" into "\" before the pattern is parsed.
    (match) => match[1].replace(/\\\\/g, "\\"),
  );

// android.os.PatternMatcher.matchGlobPattern, ported (PATTERN_SIMPLE_GLOB).
function matchGlob(pattern: string, match: string): boolean {
  const NP = pattern.length;
  if (NP <= 0) return match.length <= 0;
  const NM = match.length;
  let ip = 0;
  let im = 0;
  let nextChar = pattern.charAt(0);
  while (ip < NP && im < NM) {
    let c = nextChar;
    ip++;
    nextChar = ip < NP ? pattern.charAt(ip) : "";
    const escaped = c === "\\";
    if (escaped) {
      c = nextChar;
      ip++;
      nextChar = ip < NP ? pattern.charAt(ip) : "";
    }
    if (nextChar === "*") {
      if (!escaped && c === ".") {
        if (ip >= NP - 1) return true;
        ip++;
        nextChar = pattern.charAt(ip);
        if (nextChar === "\\") {
          ip++;
          nextChar = ip < NP ? pattern.charAt(ip) : "";
        }
        do {
          if (match.charAt(im) === nextChar) break;
          im++;
        } while (im < NM);
        if (im === NM) return false;
        ip++;
        nextChar = ip < NP ? pattern.charAt(ip) : "";
        im++;
      } else {
        do {
          if (match.charAt(im) !== c) break;
          im++;
        } while (im < NM);
        ip++;
        nextChar = ip < NP ? pattern.charAt(ip) : "";
      }
    } else {
      if (c !== "." && match.charAt(im) !== c) return false;
      im++;
    }
  }
  if (ip >= NP && im >= NM) return true;
  return ip === NP - 2 && pattern.charAt(ip) === "." && pattern.charAt(ip + 1) === "*";
}

// What Android 11 resolves: everything in the filter except pathAdvancedPattern.
function opensBelowApi31(urlPath: string): boolean {
  return (
    values("path").includes(urlPath) ||
    values("pathPrefix").some((prefix) => urlPath.startsWith(prefix)) ||
    values("pathPattern").some((pattern) => matchGlob(pattern, urlPath))
  );
}

const ADDRESS = "ZRNRW3X4WMRJZLP2UZR5PECN4A23SW7QETVR4H53F6FFG3NHC6MVSLMQPM";
const BUNDLE = "6C14ADBAC1DF55428E587D84AA7E5AE13DA464FE";

describe("App Links below API 31", () => {
  it.each([
    "/",
    `/${ADDRESS}`,
    `/${BUNDLE}`,
    "/niko.algo",
    "/sub.niko.algo",
    "/niko.algo/nfd",
    "/niko.algo/ans",
    "/faq/",
    "/features/",
    "/methodology/",
    "/about/",
    "/asm-privacy/",
    "/account-deletion/",
    "/home/",
    `/widgets/historic/${ADDRESS}`,
  ])("opens %s in the app", (urlPath) => {
    expect(opensBelowApi31(urlPath)).toBe(true);
  });

  // F4: a sign-in step must never be handed from the Custom Tab to the app.
  it.each([
    "/accounts/login/",
    "/accounts/apple/login/callback/",
    "/accounts/apple/login/callback/finish/",
    "/accounts/google/login/callback/",
    "/accounts/twitter_oauth2/login/callback/",
    "/accounts/3rdparty/login/cancelled/",
    "/app/auth/return/",
    "/app/auth/start/google/",
    "/api/v2/niko.algo/",
    `/api/v2/${BUNDLE}/`,
    "/static/css/style.tw.css",
    "/subscriptions/",
  ])("leaves %s in the browser", (urlPath) => {
    expect(opensBelowApi31(urlPath)).toBe(false);
  });

  it("the glob port follows Android's non-backtracking '.*'", () => {
    expect(matchGlob("/.*\\.algo", "/sub.niko.algo")).toBe(false);
    expect(matchGlob("a*b", "aaab")).toBe(true);
    expect(matchGlob("/x.*", "/x")).toBe(true);
    expect(matchGlob("", "")).toBe(true);
    expect(matchGlob("/a.*", "/abc")).toBe(true);
    expect(matchGlob("/.*q", "/abc")).toBe(false);
  });
});
