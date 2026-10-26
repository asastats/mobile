import { readFileSync } from "node:fs";
import { join } from "node:path";

const WWW = join(__dirname, "..", "www");

/** The page as the WebView gets it, scripts left out. */
function page(): Document {
  return new DOMParser().parseFromString(
    readFileSync(join(WWW, "offline.html"), "utf8"),
    "text/html"
  );
}

describe("offline.html", () => {
  it("loads the server URL before its own script, and nothing inline", () => {
    const sources = Array.from(page().querySelectorAll("script")).map((s) => s.getAttribute("src"));
    expect(sources).toEqual(["server-url.js", "offline.js"]);
  });

  it("has the Retry button offline.js binds", () => {
    expect(page().getElementById("retry")?.textContent).toBe("Retry");
  });
});

describe("offline.js", () => {
  beforeEach(() => {
    document.body.innerHTML = '<button id="retry">Retry</button>';
    Object.defineProperty(window, "location", { value: { href: "" }, writable: true });
    delete (window as { ASASTATS_URL?: string }).ASASTATS_URL;
    jest.isolateModules(() => require("../www/offline.js"));
  });

  it("retries the server URL server-url.js set", () => {
    (window as { ASASTATS_URL?: string }).ASASTATS_URL = "http://192.168.1.20:8000";
    document.getElementById("retry")!.click();
    expect(window.location.href).toBe("http://192.168.1.20:8000");
  });

  it("falls back to the production site", () => {
    document.getElementById("retry")!.click();
    expect(window.location.href).toBe("https://www.asastats.com");
  });
});
