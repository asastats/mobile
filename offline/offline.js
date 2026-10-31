// offline.html's Retry button; capacitor.config.ts inlines this file and sets window.ASASTATS_URL.
// Native code sets window.ASASTATS_RETRY to the page that failed to load; only a page of the site is followed.
document.getElementById("retry").addEventListener("click", function () {
  var site = window.ASASTATS_URL || "https://www.asastats.com";
  var target = site;
  try {
    var failed = new URL(window.ASASTATS_RETRY || "");
    if (failed.origin === new URL(site).origin) target = failed.href;
  } catch (error) {
    // No failed page, or not a URL: the start page.
  }
  window.location.href = target;
});

// Light status bar icons on this page's dark background; the site's app.js resets them on its pages.
["SystemBars", "StatusBar"].forEach(function (name) {
  try {
    window.Capacitor.Plugins[name].setStyle({ style: "DARK" });
  } catch (error) {
    // No bridge or no such plugin (a browser, the tests): nothing to set.
  }
});
