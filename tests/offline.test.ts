import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SOURCE = join(__dirname, "..", "offline");

jest.mock("node:fs", () => ({ ...jest.requireActual("node:fs"), writeFileSync: jest.fn() }));

function offlinePage(serverUrl: string, dir?: string): string {
  let build: (url: string, dir?: string) => string = () => "";
  jest.isolateModules(() => {
    build = require("../capacitor.config").offlinePage;
  });
  return build(serverUrl, dir);
}

/** The page as the WebView gets it, scripts left out. */
function page(serverUrl = "https://www.asastats.com"): Document {
  return new DOMParser().parseFromString(offlinePage(serverUrl, SOURCE), "text/html");
}

describe("offline.html", () => {
  it("loads no other file: Android serves only the errorPath page itself", () => {
    const doc = page();
    expect(Array.from(doc.querySelectorAll("script")).map((s) => s.getAttribute("src"))).toEqual([
      null,
      null,
    ]);
    expect(doc.querySelector("img")?.getAttribute("src")).toMatch(/^data:image\/svg\+xml;base64,/);
    expect(doc.querySelectorAll("[src]:not([src^='data:']), link[href]")).toHaveLength(0);
  });

  it("sets the server URL before the Retry script", () => {
    const [url, retry] = Array.from(page("http://10.0.2.2:8000").querySelectorAll("script"));
    expect(url.textContent).toBe('window.ASASTATS_URL = "http://10.0.2.2:8000";');
    expect(retry.textContent).toContain(
      readFileSync(join(SOURCE, "offline.js"), "utf8").trim()
    );
  });

  it("cannot end its script early", () => {
    expect(offlinePage("https://x.example/</script>", SOURCE)).toContain(
      '"https://x.example/\\u003c/script>"'
    );
  });

  it("has the Retry button offline.js binds", () => {
    expect(page().getElementById("retry")?.textContent).toBe("Retry");
  });

  it("refuses a template that lost a tag it inlines", () => {
    const dir = mkdtempSync(join(tmpdir(), "offline-"));
    for (const name of ["offline.js", "asastats-logo.svg"]) {
      jest.requireActual("node:fs").copyFileSync(join(SOURCE, name), join(dir, name));
    }
    jest
      .requireActual("node:fs")
      .writeFileSync(join(dir, "offline.html"), "<script src='offline.js'></script>");
    expect(() => offlinePage("https://www.asastats.com", dir)).toThrow(
      'offline.html has no <script src="server-url.js"></script>'
    );
  });

  it("is what the config writes for the WebView", () => {
    offlinePage("https://www.asastats.com");
    expect(writeFileSync).toHaveBeenCalledWith("www/offline.html", expect.any(String));
  });
});

describe("offline.js", () => {
  beforeEach(() => {
    document.body.innerHTML = '<button id="retry">Retry</button>';
    Object.defineProperty(window, "location", { value: { href: "" }, writable: true });
    delete (window as { ASASTATS_URL?: string }).ASASTATS_URL;
    jest.isolateModules(() => require("../offline/offline.js"));
  });

  it("retries the server URL the page sets", () => {
    (window as { ASASTATS_URL?: string }).ASASTATS_URL = "http://192.168.1.20:8000";
    document.getElementById("retry")!.click();
    expect(window.location.href).toBe("http://192.168.1.20:8000");
  });

  it("falls back to the production site", () => {
    document.getElementById("retry")!.click();
    expect(window.location.href).toBe("https://www.asastats.com");
  });
});
