import XCTest
@testable import WebAuthPlugin

private let server = URL(string: "https://www.asastats.com")
private let challenge = String(repeating: "c", count: 43)
private let callback = URL(string: "https://www.asastats.com/app/auth/return/?ticket=t-1")!

final class FakeSession: AuthSessionStarting {
    var supported = true
    var started: (url: URL, host: String, path: String)?
    var completion: ((Result<URL, WebAuthFailure>) -> Void)?

    func start(
        url: URL, callbackHost: String, callbackPath: String,
        completion: @escaping (Result<URL, WebAuthFailure>) -> Void
    ) -> Bool {
        guard supported else { return false }
        started = (url, callbackHost, callbackPath)
        self.completion = completion
        return true
    }
}

final class WebAuthRequestTests: XCTestCase {
    func testBuildsTheStartURLFromTheServer() {
        let request = WebAuthRequest(
            server: server, provider: "google", challenge: challenge, next: "/profile/?a=1&b=2")

        XCTAssertEqual(
            request?.startURL.absoluteString,
            "https://www.asastats.com/app/auth/start/google/?challenge=\(challenge)"
                + "&next=/profile/%3Fa%3D1%26b%3D2")
        XCTAssertEqual(request?.callbackHost, "www.asastats.com")
    }

    func testKeepsAPortAndLeavesOutAnEmptyNext() {
        let request = WebAuthRequest(
            server: URL(string: "https://staging.example:8443"), provider: "github",
            challenge: challenge, next: "")

        XCTAssertEqual(
            request?.startURL.absoluteString,
            "https://staging.example:8443/app/auth/start/github/?challenge=\(challenge)")
    }

    func testLeavesOutAMissingNext() {
        let request = WebAuthRequest(
            server: server, provider: "apple", challenge: challenge, next: nil)

        XCTAssertFalse(request!.startURL.absoluteString.contains("next="))
    }

    func testRefusesWhatJavaScriptMustNotChoose() {
        let cases: [(URL?, String?, String?)] = [
            (nil, "google", challenge),
            (URL(string: "http://www.asastats.com"), "google", challenge),
            (URL(string: "https:///nohost"), "google", challenge),
            (URL(string: "https://[::1]:8443"), "google", challenge),
            (URL(string: "https://www.asa_stats.com"), "google", challenge),
            (server, nil, challenge),
            (server, "facebook", challenge),
            (server, "google/../x", challenge),
            (server, "google", nil),
            (server, "google", "short"),
            (server, "google", String(repeating: "c", count: 44)),
            (server, "google", String(repeating: "+", count: 43)),
            (server, "google", String(repeating: "/", count: 43)),
            (server, "google", String(repeating: "é", count: 43)),
        ]
        for (url, provider, value) in cases {
            XCTAssertNil(
                WebAuthRequest(server: url, provider: provider, challenge: value, next: nil),
                "\(String(describing: url)) \(String(describing: provider)) \(String(describing: value))")
        }
    }

    func testAcceptsAnIPv4ServerForLocalBuilds() {
        let request = WebAuthRequest(
            server: URL(string: "https://192.168.1.20:8000"), provider: "google",
            challenge: challenge, next: nil)

        XCTAssertEqual(request?.callbackHost, "192.168.1.20")
    }

    func testEncodesNonAsciiAsUtf8() {
        XCTAssertEqual(WebAuthRequest.encoded("/aé b"), "/a%C3%A9%20b")
    }

    func testProvidersMatchTheServer() {
        XCTAssertEqual(
            WebAuthRequest.providers,
            ["apple", "discord", "github", "google", "reddit", "twitter_oauth2"])
        XCTAssertEqual(WebAuthRequest.callbackPath, "/app/auth/return/")
    }

    func testAcceptsOnlyItsOwnCallbackWithATicket() {
        let request = WebAuthRequest(
            server: server, provider: "google", challenge: challenge, next: nil)!

        XCTAssertTrue(request.accepts(callback))
        for text in [
            "http://www.asastats.com/app/auth/return/?ticket=t",
            "https://evil.example/app/auth/return/?ticket=t",
            "https://www.asastats.com/app/auth/return?ticket=t",
            "https://www.asastats.com/elsewhere/?ticket=t",
            "https://www.asastats.com/app/auth/return/",
            "https://www.asastats.com/app/auth/return/?ticket=",
        ] {
            XCTAssertFalse(request.accepts(URL(string: text)!), text)
        }
    }
}

final class WebAuthControllerTests: XCTestCase {
    private var session: FakeSession!
    private var controller: WebAuthController!
    private var results: [Result<URL, WebAuthFailure>] = []

    override func setUp() {
        session = FakeSession()
        controller = WebAuthController(session: session)
        results = []
    }

    private func start(provider: String? = "google") {
        controller.start(server: server, provider: provider, challenge: challenge, next: "/x/") {
            self.results.append($0)
        }
    }

    func testOpensTheSheetOnTheCallbackHostAndPath() {
        start()

        XCTAssertEqual(session.started?.host, "www.asastats.com")
        XCTAssertEqual(session.started?.path, "/app/auth/return/")
        XCTAssertTrue(controller.busy)
        XCTAssertTrue(results.isEmpty)
    }

    func testResolvesWithTheCallback() {
        start()
        session.completion?(.success(callback))

        XCTAssertEqual(try results.first?.get(), callback)
        XCTAssertFalse(controller.busy)
    }

    func testFailsOnACallbackItDoesNotAccept() {
        start()
        session.completion?(.success(URL(string: "https://evil.example/app/auth/return/?ticket=t")!))

        XCTAssertEqual(results.count, 1)
        if case .failure(let failure) = results[0] { XCTAssertEqual(failure, .failed) } else { XCTFail() }
    }

    func testPassesTheSheetsFailureOn() {
        start()
        session.completion?(.failure(.cancelled))

        if case .failure(let failure) = results[0] { XCTAssertEqual(failure, .cancelled) } else { XCTFail() }
        XCTAssertFalse(controller.busy)
    }

    func testRefusesASecondSignInWhileOneIsOpen() {
        start()
        start()

        if case .failure(let failure) = results[0] { XCTAssertEqual(failure, .busy) } else { XCTFail() }
    }

    func testRefusesAnInvalidRequestWithoutOpeningASheet() {
        start(provider: "facebook")

        if case .failure(let failure) = results[0] { XCTAssertEqual(failure, .invalid) } else { XCTFail() }
        XCTAssertNil(session.started)
        XCTAssertFalse(controller.busy)
    }

    func testReportsADeviceThatCannotVerify() {
        session.supported = false
        start()

        if case .failure(let failure) = results[0] { XCTAssertEqual(failure, .unsupported) } else { XCTFail() }
        XCTAssertFalse(controller.busy)
    }

    func testFailureRawValuesAreWhatSignInTsReads() {
        XCTAssertEqual(
            [WebAuthFailure.invalid, .busy, .unsupported, .cancelled, .failed].map(\.rawValue),
            ["invalid", "busy", "unsupported", "cancelled", "failed"])
    }
}
