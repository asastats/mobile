import { readFileSync, writeFileSync } from 'node:fs';
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

/**
 * offline/offline.html with its script, logo and the server URL inlined.
 *
 * Under server.url Android serves only the errorPath page locally; other files go to the network.
 */
export function offlinePage(serverUrl: string, dir = 'offline'): string {
  const read = (name: string) => readFileSync(`${dir}/${name}`, 'utf8');
  const url = JSON.stringify(serverUrl).replace(/</g, '\\u003c');
  const logo = Buffer.from(read('asastats-logo.svg')).toString('base64');
  const inlined: [string, string][] = [
    ['<script src="server-url.js"></script>', `<script>window.ASASTATS_URL = ${url};</script>`],
    ['<script src="offline.js"></script>', `<script>\n${read('offline.js')}</script>`],
    ['src="asastats-logo.svg"', `src="data:image/svg+xml;base64,${logo}"`],
  ];
  return inlined.reduce((page, [tag, inline]) => {
    if (!page.includes(tag)) throw new Error(`${dir}/offline.html has no ${tag}`);
    return page.replace(tag, () => inline);
  }, read('offline.html'));
}

writeFileSync('www/offline.html', offlinePage(serverUrl));

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
      // Unscaled and centred, like launch_splash.xml: the default FIT_XY stretched it.
      androidScaleType: 'CENTER',
    },
    // iOS: show an alert that arrives while the app is open, too.
    FirebaseMessaging: {
      presentationOptions: ['alert', 'badge', 'sound'],
    },
  },
  // The plugin's own README: avoids an SPM package identity collision (needs CLI 8.4+).
  experimental: {
    ios: {
      spm: {
        packageOptions: {
          '@capacitor-firebase/messaging': { symlink: true },
        },
      },
    },
  },
};

export default config;
