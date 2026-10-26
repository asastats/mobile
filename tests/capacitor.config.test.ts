import { writeFileSync } from "node:fs";
import type { CapacitorConfig } from "@capacitor/cli";

import { version } from "../package.json";

jest.mock("node:fs", () => ({ writeFileSync: jest.fn() }));

const ENV = { ...process.env };

/** Load the config afresh with `env` set, as `npx cap` does. */
function load(env: Record<string, string> = {}): CapacitorConfig {
  process.env = { ...ENV };
  delete process.env.ASASTATS_URL;
  delete process.env.ASASTATS_RELEASE;
  Object.assign(process.env, env);
  let config: CapacitorConfig | undefined;
  jest.isolateModules(() => {
    config = require("../capacitor.config").default;
  });
  return config as CapacitorConfig;
}

afterEach(() => {
  process.env = { ...ENV };
  (writeFileSync as jest.Mock).mockClear();
});

describe("capacitor.config", () => {
  it("loads the production site over https by default", () => {
    const config = load();
    expect(config.server?.url).toBe("https://www.asastats.com");
    expect(config.server?.cleartext).toBe(false);
    expect(config.server?.errorPath).toBe("offline.html");
  });

  it("allows cleartext only for an http development server", () => {
    const config = load({ ASASTATS_URL: "http://192.168.1.20:8000" });
    expect(config.server?.url).toBe("http://192.168.1.20:8000");
    expect(config.server?.cleartext).toBe(true);
  });

  it("refuses anything but http(s)", () => {
    expect(() => load({ ASASTATS_URL: "ftp://example.com" })).toThrow(
      "ASASTATS_URL must be an http(s) URL"
    );
  });

  it("refuses an http server in a release build", () => {
    expect(() =>
      load({ ASASTATS_URL: "http://192.168.1.20:8000", ASASTATS_RELEASE: "1" })
    ).toThrow("a release build needs an https ASASTATS_URL");
  });

  it("accepts an https server in a release build", () => {
    expect(load({ ASASTATS_RELEASE: "1" }).server?.url).toBe("https://www.asastats.com");
  });

  it("writes the server URL for offline.html's Retry", () => {
    load({ ASASTATS_URL: "https://staging.example" });
    expect(writeFileSync).toHaveBeenCalledWith(
      "www/server-url.js",
      'window.ASASTATS_URL = "https://staging.example";\n'
    );
  });

  it("appends the user-agent token frontend core/appclient.py parses", () => {
    const config = load();
    expect(config.ios?.appendUserAgent).toBe(`ASAStatsApp/${version} (ios)`);
    expect(config.android?.appendUserAgent).toBe(`ASAStatsApp/${version} (android)`);
  });

  it("names the store app", () => {
    const config = load();
    expect(config.appId).toBe("com.asastats.app");
    expect(config.appName).toBe("ASA Stats");
    expect(config.webDir).toBe("www");
  });
});
