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
  type Page = { ASASTATS_URL?: string; ASASTATS_RETRY?: unknown };
  /** Load the script on an offline page that native code told `failed`. */
  const load = (failed?: unknown) => {
    document.body.innerHTML = '<button id="retry">Retry</button>';
    Object.defineProperty(window, "location", { value: { href: "" }, writable: true });
    (window as Page).ASASTATS_RETRY = failed;
    jest.isolateModules(() => require("../offline/offline.js"));
  };
  const retry = (failed: unknown, site?: string) => {
    if (site) (window as Page).ASASTATS_URL = site;
    load(failed);
    document.getElementById("retry")!.click();
    return window.location.href;
  };

  beforeEach(() => {
    delete (window as { ASASTATS_URL?: string }).ASASTATS_URL;
    load();
  });

  it("returns to the page that failed to load", () => {
    const failed = "https://www.asastats.com/about/?tab=2#team";
    expect(retry(failed)).toBe(failed);
  });

  it("returns to a failed page of a local server too", () => {
    expect(
      retry("http://192.168.1.20:8000/faq/", "http://192.168.1.20:8000")
    ).toBe("http://192.168.1.20:8000/faq/");
  });

  it.each([
    ["another site", "https://evil.example/"],
    ["a look-alike host", "https://www.asastats.com.evil.example/"],
    ["a script URL", "javascript:alert(1)"],
    ["not a URL", "nonsense"],
    ["an empty value", ""],
    ["no value", undefined],
    ["not a string", { href: "https://www.asastats.com/x/" }],
  ])("opens the start page for %s", (_, failed) => {
    expect(retry(failed)).toBe("https://www.asastats.com");
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
