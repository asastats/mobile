package com.asastats.app;

import android.content.res.Configuration;
import android.os.Bundle;
import android.webkit.CookieManager;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import com.getcapacitor.Bridge;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.BridgeWebViewClient;
import org.json.JSONObject;

public class MainActivity extends BridgeActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        bridge.setWebViewClient(new SiteErrorPagesClient(bridge));
        AlertMessagingService.createChannel(this);
    }

    /** The WebView writes cookies to disk lazily; a killed app would come back with an older session (docs/logbook.md). */
    @Override
    public void onPause() {
        super.onPause();
        CookieManager.getInstance().flush();
    }

    /** fontScale is in configChanges, and the WebView reads the text size only when created (docs/logbook.md). */
    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        bridge.getWebView().getSettings().setTextZoom(Math.round(newConfig.fontScale * 100));
    }

    /** offline.html only when the site cannot be reached; its own 404/5xx pages show (docs/logbook.md). */
    static class SiteErrorPagesClient extends BridgeWebViewClient {

        /** BridgeWebViewClient keeps its own private. */
        private final Bridge bridge;

        SiteErrorPagesClient(Bridge bridge) {
            super(bridge);
            this.bridge = bridge;
        }

        @Override
        public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse errorResponse) {
            // Not super: it loads errorPath for every HTTP error status.
        }

        /** The page that failed; offline.html gets it once loaded, for Retry (offline/offline.js). */
        private String failedPage;

        /** As Capacitor's, keeping the failed page for onPageFinished (docs/logbook.md). */
        @Override
        public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
            // Not super: same load, minus WebViewListener calls (package-private; none listens here).
            // The bare errorUrl: the local server serves it only by that exact URL.
            String errorUrl = bridge.getErrorUrl();
            if (errorUrl != null && request.isForMainFrame()) {
                String page = request.getUrl().toString();
                // The error page's own failure keeps the earlier page and cannot loop.
                if (!page.startsWith(errorUrl)) failedPage = page;
                view.loadUrl(errorUrl);
            }
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            String errorUrl = bridge.getErrorUrl();
            if (errorUrl != null && url != null && url.startsWith(errorUrl) && failedPage != null) {
                view.evaluateJavascript(retryScript(failedPage), null);
            }
        }

        /** The URL as a JSON string literal, so nothing in it can end the statement. */
        static String retryScript(String page) {
            return "window.ASASTATS_RETRY = " + JSONObject.quote(page) + ";";
        }
    }
}
