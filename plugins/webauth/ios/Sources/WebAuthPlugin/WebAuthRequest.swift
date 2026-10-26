import Foundation

/// Why a sign-in did not return a callback; the raw value is the JS error message
/// `signIn.ts` reads.
public enum WebAuthFailure: String, Error {
    case invalid, busy, unsupported, cancelled, failed
}

/// One sign-in, checked before any sheet opens. Every page of the site can call
/// the plugin, so nothing from JavaScript reaches the URL unchecked.
public struct WebAuthRequest {
    /// Must match `PROVIDERS` in frontend `core/views_appauth.py`.
    public static let providers: Set<String> = [
        "apple", "discord", "github", "google", "reddit", "twitter_oauth2"
    ]
    /// Must match the frontend's `app_auth_return` URL.
    public static let callbackPath = "/app/auth/return/"

    public let startURL: URL
    public let callbackHost: String

    /// - Returns: nil unless the server is https on a DNS name or IPv4 address and
    ///   every value is well formed.
    public init?(server: URL?, provider: String?, challenge: String?, next: String?) {
        guard let server = server, server.scheme == "https",
              let host = server.host, WebAuthRequest.isHost(host),
              let provider = provider, WebAuthRequest.providers.contains(provider),
              let challenge = challenge, WebAuthRequest.isChallenge(challenge)
        else { return nil }

        var query = "challenge=\(challenge)"
        if let next = next, !next.isEmpty {
            query += "&next=\(WebAuthRequest.encoded(next))"
        }
        let port = server.port.map { ":\($0)" } ?? ""
        // Every part is checked or encoded above, so this always parses.
        startURL = URL(string: "https://\(host)\(port)/app/auth/start/\(provider)/?\(query)")!
        callbackHost = host
    }

    /// Whether `url` is this request's callback carrying a ticket.
    public func accepts(_ url: URL) -> Bool {
        guard let parts = URLComponents(url: url, resolvingAgainstBaseURL: false),
              parts.scheme == "https", parts.host == callbackHost,
              parts.path == WebAuthRequest.callbackPath
        else { return false }
        let ticket = parts.queryItems?.first { $0.name == "ticket" }?.value ?? ""
        return !ticket.isEmpty
    }

    /// base64url SHA-256 without padding: 43 of `A-Z a-z 0-9 - _`.
    static func isChallenge(_ value: String) -> Bool {
        value.unicodeScalars.count == 43
            && value.unicodeScalars.allSatisfy { base64url.contains($0) }
    }

    /// Letters, digits, dots and hyphens; an IPv6 host comes without its brackets.
    static func isHost(_ value: String) -> Bool {
        !value.isEmpty && value.unicodeScalars.allSatisfy { hostCharacters.contains($0) }
    }

    /// Percent-encode everything but unreserved characters and `/`.
    static func encoded(_ value: String) -> String {
        value.addingPercentEncoding(withAllowedCharacters: safe) ?? ""
    }

    private static let base64url = CharacterSet(
        charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    )
    private static let safe = base64url.union(CharacterSet(charactersIn: ".~/"))
    private static let hostCharacters = CharacterSet(
        charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-"
    )
}

/// Opens the system sheet; the real one is `SystemAuthSession`, tests use a fake.
public protocol AuthSessionStarting: AnyObject {
    /// - Returns: false when this device cannot verify an https callback.
    func start(
        url: URL, callbackHost: String, callbackPath: String,
        completion: @escaping (Result<URL, WebAuthFailure>) -> Void
    ) -> Bool
}

/// One sign-in at a time, and only a callback the request accepts.
public final class WebAuthController {
    private let session: AuthSessionStarting
    public private(set) var busy = false

    public init(session: AuthSessionStarting) {
        self.session = session
    }

    public func start(
        server: URL?, provider: String?, challenge: String?, next: String?,
        completion: @escaping (Result<URL, WebAuthFailure>) -> Void
    ) {
        guard !busy else { return completion(.failure(.busy)) }
        guard let request = WebAuthRequest(
            server: server, provider: provider, challenge: challenge, next: next)
        else { return completion(.failure(.invalid)) }

        busy = true
        let started = session.start(
            url: request.startURL, callbackHost: request.callbackHost,
            callbackPath: WebAuthRequest.callbackPath
        ) { [weak self] result in
            self?.busy = false
            switch result {
            case .success(let url):
                completion(request.accepts(url) ? .success(url) : .failure(.failed))
            case .failure(let failure):
                completion(.failure(failure))
            }
        }
        if !started {
            busy = false
            completion(.failure(.unsupported))
        }
    }
}
