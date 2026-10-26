package com.asastats.webauth;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.junit.Before;
import org.junit.Test;

public class WebAuthTest {

    private static final String SERVER = "https://www.asastats.com";
    private static final String CHALLENGE = "c".repeat(43);
    private static final String CALLBACK = SERVER + "/app/auth/return/?ticket=t-1";

    // --- WebAuthRequest

    @Test
    public void buildsTheStartUrlFromTheServer() {
        WebAuthRequest request = WebAuthRequest.create(SERVER, "google", CHALLENGE, "/profile/?a=1&b=2");

        assertEquals(
            SERVER + "/app/auth/start/google/?challenge=" + CHALLENGE + "&next=/profile/%3Fa%3D1%26b%3D2",
            request.startUrl
        );
        assertEquals("www.asastats.com", request.callbackHost);
    }

    @Test
    public void keepsAPortAndLeavesOutAnEmptyOrMissingNext() {
        assertEquals(
            "https://staging.example:8443/app/auth/start/github/?challenge=" + CHALLENGE,
            WebAuthRequest.create("https://staging.example:8443", "github", CHALLENGE, "").startUrl
        );
        assertFalse(WebAuthRequest.create(SERVER, "apple", CHALLENGE, null).startUrl.contains("next="));
    }

    @Test
    public void encodesNonAsciiAsUtf8() {
        assertEquals("/a%C3%A9%20b", WebAuthRequest.encoded("/aé b"));
    }

    @Test
    public void refusesWhatJavaScriptMustNotChoose() {
        String[][] cases = {
            {null, "google", CHALLENGE},
            {"http://www.asastats.com", "google", CHALLENGE},
            {"https:///nohost", "google", CHALLENGE},
            {"https://bad host", "google", CHALLENGE},
            {SERVER, null, CHALLENGE},
            {SERVER, "facebook", CHALLENGE},
            {SERVER, "google/../x", CHALLENGE},
            {SERVER, "google", null},
            {SERVER, "google", "short"},
            {SERVER, "google", "c".repeat(44)},
            {SERVER, "google", "+".repeat(43)},
            {SERVER, "google", "/".repeat(43)},
        };
        for (String[] c : cases) {
            assertNull(String.join(" ", String.valueOf(c[0]), c[1], c[2]),
                WebAuthRequest.create(c[0], c[1], c[2], null));
        }
    }

    @Test
    public void providersAndCallbackMatchTheServer() {
        assertEquals(
            Set.of("apple", "discord", "github", "google", "reddit", "twitter_oauth2"),
            WebAuthRequest.PROVIDERS
        );
        assertEquals("/app/auth/return/", WebAuthRequest.CALLBACK_PATH);
    }

    @Test
    public void acceptsOnlyItsOwnCallbackWithATicket() {
        WebAuthRequest request = WebAuthRequest.create(SERVER, "google", CHALLENGE, null);

        assertTrue(request.accepts(CALLBACK));
        assertTrue(request.accepts(SERVER + "/app/auth/return/?x=1&ticket=t"));
        String[] refused = {
            "http://www.asastats.com/app/auth/return/?ticket=t",
            "https://evil.example/app/auth/return/?ticket=t",
            SERVER + "/app/auth/return?ticket=t",
            SERVER + "/elsewhere/?ticket=t",
            SERVER + "/app/auth/return/",
            SERVER + "/app/auth/return/?ticket=",
            SERVER + "/app/auth/return/?other=t",
            "not a url",
            null,
        };
        for (String url : refused) {
            assertFalse(String.valueOf(url), request.accepts(url));
        }
    }

    // --- WebAuthController

    private static final class FakeLauncher implements WebAuthController.Launcher {
        boolean supported = true;
        String url;
        String host;
        String path;
        WebAuthController.Callback callback;

        @Override
        public boolean launch(String url, String host, String path, WebAuthController.Callback callback) {
            if (!supported) return false;
            this.url = url;
            this.host = host;
            this.path = path;
            this.callback = callback;
            return true;
        }
    }

    private FakeLauncher launcher;
    private WebAuthController controller;
    private List<String[]> results;

    @Before
    public void setUp() {
        launcher = new FakeLauncher();
        controller = new WebAuthController(launcher);
        results = new ArrayList<>();
    }

    private void start(String provider) {
        controller.start(SERVER, provider, CHALLENGE, "/x/", (url, failure) -> results.add(new String[] {url, failure}));
    }

    @Test
    public void opensTheTabOnTheCallbackHostAndPath() {
        start("google");

        assertEquals("www.asastats.com", launcher.host);
        assertEquals("/app/auth/return/", launcher.path);
        assertTrue(launcher.url.startsWith(SERVER + "/app/auth/start/google/"));
        assertTrue(controller.isBusy());
        assertTrue(results.isEmpty());
    }

    @Test
    public void resolvesWithTheCallback() {
        start("google");
        launcher.callback.done(CALLBACK, null);

        assertEquals(CALLBACK, results.get(0)[0]);
        assertNull(results.get(0)[1]);
        assertFalse(controller.isBusy());
    }

    @Test
    public void failsOnACallbackItDoesNotAccept() {
        start("google");
        launcher.callback.done("https://evil.example/app/auth/return/?ticket=t", null);

        assertEquals(WebAuthController.FAILED, results.get(0)[1]);
    }

    @Test
    public void passesTheTabsFailureOn() {
        start("google");
        launcher.callback.done(null, WebAuthController.CANCELLED);

        assertEquals(WebAuthController.CANCELLED, results.get(0)[1]);
        assertFalse(controller.isBusy());
    }

    @Test
    public void refusesASecondSignInWhileOneIsOpen() {
        start("google");
        start("google");

        assertEquals(WebAuthController.BUSY, results.get(0)[1]);
    }

    @Test
    public void refusesAnInvalidRequestWithoutOpeningATab() {
        start("facebook");

        assertEquals(WebAuthController.INVALID, results.get(0)[1]);
        assertNull(launcher.url);
        assertFalse(controller.isBusy());
    }

    @Test
    public void reportsADeviceThatCannotVerify() {
        launcher.supported = false;
        start("google");

        assertEquals(WebAuthController.UNSUPPORTED, results.get(0)[1]);
        assertFalse(controller.isBusy());
    }

    @Test
    public void failureNamesAreWhatSignInTsReads() {
        assertEquals("invalid busy unsupported cancelled failed", String.join(" ",
            WebAuthController.INVALID, WebAuthController.BUSY, WebAuthController.UNSUPPORTED,
            WebAuthController.CANCELLED, WebAuthController.FAILED));
    }
}
