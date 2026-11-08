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

  it("has the title and hint offline.js swaps", () => {
    expect(page().getElementById("title")?.textContent).toBe("No connection");
    expect(page().getElementById("hint")).not.toBeNull();
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

const PAGE =
  '<h1 id="title">No connection</h1><p id="hint">Check</p><button id="retry">Retry</button>';

describe("offline.js", () => {
  type Page = { ASASTATS_URL?: string; ASASTATS_RETRY?: unknown };
  const page = window as unknown as Page;
  const replace = jest.fn();
  const fetchMock = jest.fn();
  const removers: (() => void)[] = [];

  const flush = async () => {
    await Promise.resolve();
    await Promise.resolve();
  };
  const setVisibility = (state: string) =>
    Object.defineProperty(document, "visibilityState", { configurable: true, value: state });
  const element = (id: string) => document.getElementById(id) as HTMLElement;

  /** Load the script on an offline page that native code told `failed`. */
  const load = (failed?: unknown) => {
    document.body.innerHTML = PAGE;
    page.ASASTATS_RETRY = failed;
    jest.isolateModules(() => require("../offline/offline.js"));
  };

  beforeAll(() => {
    Object.defineProperty(window, "location", { value: { replace }, writable: true });
    (window as unknown as { fetch: jest.Mock }).fetch = fetchMock;
    // Each load adds listeners to the one jsdom window: drop them with the test.
    for (const target of [window, document]) {
      const add = target.addEventListener.bind(target);
      jest.spyOn(target, "addEventListener").mockImplementation((type: string, listener: any) => {
        add(type, listener);
        removers.push(() => target.removeEventListener(type, listener));
      });
    }
  });

  beforeEach(() => {
    jest.useFakeTimers();
    replace.mockClear();
    fetchMock.mockReset();
    fetchMock.mockRejectedValue(new TypeError("offline"));
    sessionStorage.clear();
    setVisibility("visible");
    delete page.ASASTATS_URL;
  });

  afterEach(() => {
    removers.splice(0).forEach((remove) => remove());
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  describe("Retry", () => {
    const retry = (failed: unknown, site?: string) => {
      if (site) page.ASASTATS_URL = site;
      load(failed);
      element("retry").click();
      return replace.mock.calls[0][0];
    };

    it("returns to the page that failed to load", () => {
      const failed = "https://www.asastats.com/about/?tab=2#team";
      expect(retry(failed)).toBe(failed);
    });

    it("returns to a failed page of a local server too", () => {
      expect(retry("http://192.168.1.20:8000/faq/", "http://192.168.1.20:8000")).toBe(
        "http://192.168.1.20:8000/faq/"
      );
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
      expect(retry(undefined, "http://192.168.1.20:8000")).toBe("http://192.168.1.20:8000");
    });

    it("falls back to the production site", () => {
      expect(retry(undefined)).toBe("https://www.asastats.com");
    });
  });

  describe("reconnecting", () => {
    it("says so first, with no message or button to act on", () => {
      load();
      expect(element("title").textContent).toBe("Reconnecting…");
      expect(element("hint").hidden).toBe(true);
      expect(element("retry").hidden).toBe(true);
    });

    it("says No connection once the grace is over", () => {
      load();
      jest.advanceTimersByTime(6000);
      expect(element("title").textContent).toBe("No connection");
      expect(element("hint").hidden).toBe(false);
      expect(element("retry").hidden).toBe(false);
    });

    it("says No connection at once right after a return that failed", () => {
      sessionStorage.setItem("asastats.offlineReturnedAt", String(Date.now()));
      load();
      expect(element("title").textContent).toBe("No connection");
      expect(element("retry").hidden).toBe(false);
    });

    it("starts the grace over when the reader comes back", () => {
      load();
      jest.advanceTimersByTime(6000);
      document.dispatchEvent(new Event("visibilitychange"));
      expect(element("title").textContent).toBe("Reconnecting…");
      expect(fetchMock).toHaveBeenCalled();
    });

    it("does nothing when the page goes to the background", () => {
      load();
      jest.advanceTimersByTime(6000);
      fetchMock.mockClear();
      setVisibility("hidden");
      document.dispatchEvent(new Event("visibilitychange"));
      expect(element("title").textContent).toBe("No connection");
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it("asks at once when the network comes back", () => {
      load();
      expect(fetchMock).not.toHaveBeenCalled();
      window.dispatchEvent(new Event("online"));
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
  });

  describe("the way back", () => {
    const failed = "https://www.asastats.com/about/";

    it("asks the site for a small file, past every cache", () => {
      page.ASASTATS_URL = "http://192.168.1.20:8000";
      load();
      jest.advanceTimersByTime(500);
      expect(fetchMock).toHaveBeenCalledWith("http://192.168.1.20:8000/favicon-16x16.png", {
        mode: "no-cors",
        cache: "no-store",
      });
    });

    it("waits for native code before the first question", () => {
      load(failed);
      jest.advanceTimersByTime(499);
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it("returns to the failed page as soon as the site answers", async () => {
      fetchMock.mockResolvedValue({});
      load(failed);
      jest.advanceTimersByTime(500);
      await flush();
      expect(replace).toHaveBeenCalledTimes(1);
      expect(replace).toHaveBeenCalledWith(failed);
    });

    it("keeps asking while the site does not answer", async () => {
      load(failed);
      jest.advanceTimersByTime(4500);
      await flush();
      expect(fetchMock).toHaveBeenCalledTimes(3);
      expect(replace).not.toHaveBeenCalled();
    });

    it("returns once for two answers", async () => {
      fetchMock.mockResolvedValue({});
      load(failed);
      jest.advanceTimersByTime(2000);
      await flush();
      expect(fetchMock).toHaveBeenCalledTimes(2);
      expect(replace).toHaveBeenCalledTimes(1);
    });

    it("does not ask from the background", () => {
      setVisibility("hidden");
      load(failed);
      jest.advanceTimersByTime(4500);
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it("stays when the app went to the background during the question", async () => {
      fetchMock.mockResolvedValue({});
      load(failed);
      jest.advanceTimersByTime(500);
      setVisibility("hidden");
      await flush();
      expect(replace).not.toHaveBeenCalled();
    });

    it("does not reload in a loop when the site answers but the page fails", async () => {
      sessionStorage.setItem("asastats.offlineReturnedAt", String(Date.now()));
      fetchMock.mockResolvedValue({});
      load(failed);
      jest.advanceTimersByTime(8000);
      await flush();
      expect(replace).not.toHaveBeenCalled();
    });

    it("tries again once the loop guard is over", async () => {
      sessionStorage.setItem("asastats.offlineReturnedAt", String(Date.now() - 10000));
      fetchMock.mockResolvedValue({});
      load(failed);
      jest.advanceTimersByTime(500);
      await flush();
      expect(replace).toHaveBeenCalledWith(failed);
    });

    it("still works without storage", async () => {
      const blocked = () => {
        throw new Error("blocked");
      };
      const get = jest.spyOn(Storage.prototype, "getItem").mockImplementation(blocked);
      const set = jest.spyOn(Storage.prototype, "setItem").mockImplementation(blocked);
      fetchMock.mockResolvedValue({});
      load(failed);
      expect(element("title").textContent).toBe("Reconnecting…");
      jest.advanceTimersByTime(500);
      await flush();
      expect(replace).toHaveBeenCalledWith(failed);
      get.mockRestore();
      set.mockRestore();
    });
  });

  describe("status bar", () => {
    type Bridge = { Capacitor?: unknown };
    afterEach(() => {
      delete (window as Bridge).Capacitor;
    });

    it("asks for light icons on the dark page", () => {
      const setStyle = jest.fn();
      (window as Bridge).Capacitor = {
        Plugins: { StatusBar: { setStyle }, SystemBars: { setStyle } },
      };
      load();
      expect(setStyle).toHaveBeenCalledTimes(2);
      expect(setStyle).toHaveBeenCalledWith({ style: "DARK" });
    });

    it("does nothing without the bridge", () => {
      expect(load).not.toThrow();
    });
  });
});
