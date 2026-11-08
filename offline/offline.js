// offline.html's Retry button and its quiet way back; capacitor.config.ts inlines this file and sets window.ASASTATS_URL.
// Native code sets window.ASASTATS_RETRY to the page that failed to load; only a page of the site is followed.
// Why it says "Reconnecting" first: docs/logbook.md.
var GRACE_MS = 6000;
var PROBE_MS = 2000;
var FIRST_PROBE_MS = 500; // after native code has set ASASTATS_RETRY
var RETURN_AGAIN_MS = 10000; // the site answers but the page fails: no reload loop
var RETURNED_AT = "asastats.offlineReturnedAt";

var title = document.getElementById("title");
var hint = document.getElementById("hint");
var retry = document.getElementById("retry");
var graceTimer;

function site() {
  return window.ASASTATS_URL || "https://www.asastats.com";
}

function target() {
  try {
    var failed = new URL(window.ASASTATS_RETRY || "");
    if (failed.origin === new URL(site()).origin) return failed.href;
  } catch (error) {
    // No failed page, or not a URL: the start page.
  }
  return site();
}

function returnedAt() {
  try {
    return Number(window.sessionStorage.getItem(RETURNED_AT)) || 0;
  } catch (error) {
    return 0;
  }
}

function justReturned() {
  return Date.now() - returnedAt() < RETURN_AGAIN_MS;
}

function noConnection() {
  title.textContent = "No connection";
  hint.hidden = false;
  retry.hidden = false;
}

function reconnecting() {
  if (justReturned()) return;
  title.textContent = "Reconnecting…";
  hint.hidden = true;
  retry.hidden = true;
  clearTimeout(graceTimer);
  graceTimer = setTimeout(noConnection, GRACE_MS);
}

function returnToSite() {
  if (document.visibilityState === "hidden" || justReturned()) return;
  try {
    window.sessionStorage.setItem(RETURNED_AT, String(Date.now()));
  } catch (error) {
    // No storage: no loop guard, the page still returns.
  }
  window.location.replace(target());
}

// Any answer counts, a 404 or 502 too: the site's own page then shows. Opaque, so no CORS.
function probe() {
  if (document.visibilityState === "hidden") return;
  window.fetch(site() + "/favicon-16x16.png", { mode: "no-cors", cache: "no-store" }).then(
    returnToSite,
    function () {
      // Not reachable yet: the next tick asks again.
    }
  );
}

function comeBack() {
  if (document.visibilityState === "hidden") return;
  reconnecting();
  probe();
}

retry.addEventListener("click", function () {
  window.location.replace(target());
});
document.addEventListener("visibilitychange", comeBack);
window.addEventListener("online", comeBack);
reconnecting();
setTimeout(probe, FIRST_PROBE_MS);
setInterval(probe, PROBE_MS);

// Light status bar icons on this page's dark background; the site's app.js resets them on its pages.
["SystemBars", "StatusBar"].forEach(function (name) {
  try {
    window.Capacitor.Plugins[name].setStyle({ style: "DARK" });
  } catch (error) {
    // No bridge or no such plugin (a browser, the tests): nothing to set.
  }
});
