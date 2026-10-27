package com.asastats.app;

import android.content.res.Configuration;
import android.os.Bundle;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import com.getcapacitor.Bridge;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.BridgeWebViewClient;

public class MainActivity extends BridgeActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        bridge.setWebViewClient(new SiteErrorPagesClient(bridge));
    }

    /** fontScale is in configChanges, and the WebView reads the text size only when created (docs/logbook.md). */
    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        bridge.getWebView().getSettings().setTextZoom(Math.round(newConfig.fontScale * 100));
    }

    /** offline.html only when the site cannot be reached; its own 404/5xx pages show (docs/logbook.md). */
    static class SiteErrorPagesClient extends BridgeWebViewClient {

        SiteErrorPagesClient(Bridge bridge) {
            super(bridge);
        }

        @Override
        public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse errorResponse) {
            // Not super: it loads errorPath for every HTTP error status.
        }
    }
}
