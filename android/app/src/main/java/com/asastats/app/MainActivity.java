package com.asastats.app;

import android.content.res.Configuration;
import android.net.Uri;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.RenderProcessGoneDetail;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import com.getcapacitor.Bridge;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.BridgeWebViewClient;
import org.json.JSONObject;

public class MainActivity extends BridgeActivity {

    /** The page to reopen after the WebView's renderer died; in the bundle only for that restart. */
    static final String RENDERER_PAGE = "asastats_renderer_page";

    /** A second loss within this time gives up: the page itself may be what crashes it. */
    static final long RENDERER_RETRY_MS = 10_000;

    /** Static: it must survive recreate(). */
    private static long lastRendererRestart = -RENDERER_RETRY_MS;

    private String rendererPage;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        bridge.setWebViewClient(new SiteErrorPagesClient(bridge));
        AlertMessagingService.createChannel(this);
        String page = savedInstanceState == null ? null : savedInstanceState.getString(RENDERER_PAGE);
        if (isSitePage(page, bridge.getServerUrl())) {
            bridge.getWebView().loadUrl(page);
        }
    }

    @Override
    public void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        if (rendererPage != null) outState.putString(RENDERER_PAGE, rendererPage);
    }

    /**
     * Android killed or crashed the WebView's renderer: rebuild the screen on `page`
     * instead of letting Android close the app (docs/logbook.md).
     *
     * @return false when it happened again too soon, which closes the app as before
     */
    boolean restartAfterRendererLoss(WebView view, String page) {
        long now = SystemClock.elapsedRealtime();
        if (now - lastRendererRestart < RENDERER_RETRY_MS) return false;
        lastRendererRestart = now;
        rendererPage = page;
        // The dead WebView must not be used again; destroyed, later calls are ignored.
        if (view.getParent() instanceof ViewGroup) ((ViewGroup) view.getParent()).removeView(view);
        view.destroy();
        recreate();
        return true;
    }

    /** Only pages of the site itself are reopened. */
    static boolean isSitePage(String page, String serverUrl) {
        if (page == null || serverUrl == null) return false;
        Uri site = Uri.parse(serverUrl);
        Uri url = Uri.parse(page);
        return site.getScheme() != null
            && site.getScheme().equals(url.getScheme())
            && site.getAuthority() != null
            && site.getAuthority().equals(url.getAuthority());
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

        /** The site page the reader is on, for a renderer restart; the error page never counts. */
        private String currentPage;

        @Override
        public void doUpdateVisitedHistory(WebView view, String url, boolean isReload) {
            super.doUpdateVisitedHistory(view, url, isReload);
            if (isSitePage(url, bridge.getServerUrl())) currentPage = url;
        }

        @Override
        public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {
            if (super.onRenderProcessGone(view, detail)) return true;
            return bridge.getActivity() instanceof MainActivity
                && ((MainActivity) bridge.getActivity()).restartAfterRendererLoss(view, currentPage);
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
