package com.asastats.webauth;

import java.net.URI;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * One sign-in, checked before any tab opens. Every page of the site can call the
 * plugin, so nothing from JavaScript reaches the URL unchecked.
 */
public final class WebAuthRequest {

    /** Must match {@code PROVIDERS} in frontend {@code core/views_appauth.py}. */
    public static final Set<String> PROVIDERS = Set.of(
        "apple", "discord", "github", "google", "reddit", "twitter_oauth2"
    );

    /** Must match the frontend's {@code app_auth_return} URL. */
    public static final String CALLBACK_PATH = "/app/auth/return/";

    private static final Pattern CHALLENGE = Pattern.compile("^[A-Za-z0-9_-]{43}$");
    /** A DNS name or IPv4 address; an IPv6 host keeps its brackets in {@link URI#getHost}. */
    private static final Pattern HOST = Pattern.compile("^[A-Za-z0-9.-]+$");
    private static final String UNRESERVED =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~/";

    public final String startUrl;
    public final String callbackHost;

    private WebAuthRequest(String startUrl, String callbackHost) {
        this.startUrl = startUrl;
        this.callbackHost = callbackHost;
    }

    /**
     * @return null unless the server is https on a DNS name or IPv4 address and every
     *     value is well formed.
     */
    public static WebAuthRequest create(String server, String provider, String challenge, String next) {
        if (server == null || provider == null || !PROVIDERS.contains(provider)) return null;
        if (challenge == null || !CHALLENGE.matcher(challenge).matches()) return null;
        URI uri;
        try {
            uri = new URI(server);
        } catch (URISyntaxException e) {
            return null;
        }
        if (!"https".equals(uri.getScheme()) || uri.getHost() == null) return null;
        if (!HOST.matcher(uri.getHost()).matches()) return null;

        String port = uri.getPort() == -1 ? "" : ":" + uri.getPort();
        StringBuilder url = new StringBuilder("https://")
            .append(uri.getHost()).append(port)
            .append("/app/auth/start/").append(provider)
            .append("/?challenge=").append(challenge);
        if (next != null && !next.isEmpty()) url.append("&next=").append(encoded(next));
        return new WebAuthRequest(url.toString(), uri.getHost());
    }

    /** Whether {@code url} is this request's callback carrying a ticket. */
    public boolean accepts(String url) {
        URI uri;
        try {
            uri = new URI(url);
        } catch (URISyntaxException | NullPointerException e) {
            return false;
        }
        if (!"https".equals(uri.getScheme()) || !callbackHost.equals(uri.getHost())) return false;
        if (!CALLBACK_PATH.equals(uri.getRawPath()) || uri.getRawQuery() == null) return false;
        for (String pair : uri.getRawQuery().split("&")) {
            if (pair.startsWith("ticket=") && pair.length() > "ticket=".length()) return true;
        }
        return false;
    }

    /** Percent-encode everything but unreserved characters and {@code /}, as UTF-8. */
    static String encoded(String value) {
        StringBuilder out = new StringBuilder();
        for (byte b : value.getBytes(StandardCharsets.UTF_8)) {
            char c = (char) (b & 0xff);
            if (b >= 0 && UNRESERVED.indexOf(c) >= 0) {
                out.append(c);
            } else {
                out.append(String.format("%%%02X", b & 0xff));
            }
        }
        return out.toString();
    }
}
