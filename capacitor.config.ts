import { writeFileSync } from 'node:fs';
import type { CapacitorConfig } from '@capacitor/cli';

import { version } from './package.json';

const serverUrl = process.env.ASASTATS_URL || 'https://www.asastats.com';
const isHttp = serverUrl.startsWith('http:');

if (!isHttp && !serverUrl.startsWith('https:')) {
  throw new Error(`ASASTATS_URL must be an http(s) URL, got ${serverUrl}`);
}
if (isHttp && process.env.ASASTATS_RELEASE) {
  throw new Error(`a release build needs an https ASASTATS_URL, got ${serverUrl}`);
}

// offline.html reads this to retry; iOS serves that page from capacitor://localhost.
writeFileSync(
  'www/server-url.js',
  `window.ASASTATS_URL = ${JSON.stringify(serverUrl)};\n`,
);

// Parsed server-side by frontend core/appclient.py: keep the format.
const userAgent = (platform: string) => `ASAStatsApp/${version} (${platform})`;

const config: CapacitorConfig = {
  appId: 'com.asastats.app',
  appName: 'ASA Stats',
  webDir: 'www',
  backgroundColor: '#140a2e',
  server: {
    url: serverUrl,
    cleartext: isHttp,
    errorPath: 'offline.html',
  },
  ios: {
    appendUserAgent: userAgent('ios'),
  },
  android: {
    appendUserAgent: userAgent('android'),
  },
  plugins: {
    // app.js hides it on DOMContentLoaded; auto-hide is the fallback for a failed load.
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 3000,
      backgroundColor: '#140a2e',
    },
  },
};

export default config;
