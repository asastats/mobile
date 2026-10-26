package com.asastats.webauth;

/** One sign-in at a time, and only a callback the request accepts. */
public final class WebAuthController {

    /** Failure names; {@code signIn.ts} reads them as the error message. */
    public static final String INVALID = "invalid";
    public static final String BUSY = "busy";
    public static final String UNSUPPORTED = "unsupported";
    public static final String CANCELLED = "cancelled";
    public static final String FAILED = "failed";

    /** Exactly one of {@code url} and {@code failure} is set. */
    public interface Callback {
        void done(String url, String failure);
    }

    /** Opens the Auth Tab; the real one lives in {@link WebAuthPlugin}, tests use a fake. */
    public interface Launcher {
        /** @return false when this device cannot verify an https callback. */
        boolean launch(String url, String callbackHost, String callbackPath, Callback callback);
    }

    private final Launcher launcher;
    private boolean busy;

    public WebAuthController(Launcher launcher) {
        this.launcher = launcher;
    }

    public boolean isBusy() {
        return busy;
    }

    public void start(String server, String provider, String challenge, String next, Callback callback) {
        if (busy) {
            callback.done(null, BUSY);
            return;
        }
        WebAuthRequest request = WebAuthRequest.create(server, provider, challenge, next);
        if (request == null) {
            callback.done(null, INVALID);
            return;
        }
        busy = true;
        boolean launched = launcher.launch(
            request.startUrl,
            request.callbackHost,
            WebAuthRequest.CALLBACK_PATH,
            (url, failure) -> {
                busy = false;
                if (failure != null) {
                    callback.done(null, failure);
                } else if (request.accepts(url)) {
                    callback.done(url, null);
                } else {
                    callback.done(null, FAILED);
                }
            }
        );
        if (!launched) {
            busy = false;
            callback.done(null, UNSUPPORTED);
        }
    }
}
