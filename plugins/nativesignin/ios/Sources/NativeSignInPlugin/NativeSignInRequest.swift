import CryptoKit
import Foundation

/// Why a sign-in did not return a token; the raw value is the JS error message
/// `signIn.ts` reads (the Android plugin uses the same).
public enum NativeSignInFailure: String, Error {
    case invalid, busy, cancelled, unavailable, failed
}

/// One native sign-in, checked before any sheet opens. Every page of the site can
/// call the plugin, so nothing from JavaScript reaches a sheet unchecked.
public struct NativeSignInRequest {
    /// Must match `NATIVE_PROVIDERS` in frontend `core/views_appnative.py`.
    public static let providers: Set<String> = ["apple", "google"]

    /// `ASAuthorizationError.Code.canceled` and `GIDSignInError.Code.canceled`.
    static let appleCancelled = 1001
    static let googleCancelled = -5

    public let provider: String
    public let nonce: String
    /// Google only: the website's client (the token's audience) and ours.
    public let serverClientId: String?
    public let iosClientId: String?

    /// - Returns: nil unless every value is well formed; Google also needs both
    ///   client ids.
    public init?(provider: String?, nonce: String?, serverClientId: String?, iosClientId: String?) {
        guard let provider = provider, NativeSignInRequest.providers.contains(provider),
              let nonce = nonce, NativeSignInRequest.isNonce(nonce)
        else { return nil }
        if provider == "google" {
            guard NativeSignInRequest.isClientId(serverClientId),
                  NativeSignInRequest.isClientId(iosClientId)
            else { return nil }
        }
        self.provider = provider
        self.nonce = nonce
        self.serverClientId = serverClientId
        self.iosClientId = iosClientId
    }

    /// What Apple's sheet gets: hex SHA-256 of the nonce, which the token carries.
    public var hashedNonce: String {
        SHA256.hash(data: Data(nonce.utf8)).map { String(format: "%02x", $0) }.joined()
    }

    public static func failure(appleErrorCode: Int?) -> NativeSignInFailure {
        appleErrorCode == appleCancelled ? .cancelled : .failed
    }

    public static func failure(googleErrorCode: Int?) -> NativeSignInFailure {
        googleErrorCode == googleCancelled ? .cancelled : .failed
    }

    /// The server's `secrets.token_urlsafe(32)`: 43 of `A-Z a-z 0-9 - _`.
    static func isNonce(_ value: String) -> Bool {
        value.unicodeScalars.count == 43
            && value.unicodeScalars.allSatisfy { base64url.contains($0) }
    }

    /// `<digits>-<lowercase letters and digits>.apps.googleusercontent.com`.
    static func isClientId(_ value: String?) -> Bool {
        guard let value = value else { return false }
        let suffix = ".apps.googleusercontent.com"
        guard value.hasSuffix(suffix) else { return false }
        let parts = value.dropLast(suffix.count).split(separator: "-", omittingEmptySubsequences: false)
        return parts.count == 2
            && !parts[0].isEmpty && parts[0].unicodeScalars.allSatisfy { digits.contains($0) }
            && !parts[1].isEmpty && parts[1].unicodeScalars.allSatisfy { lowerAlnum.contains($0) }
    }

    private static let base64url = CharacterSet(
        charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    private static let digits = CharacterSet(charactersIn: "0123456789")
    private static let lowerAlnum = CharacterSet(charactersIn: "abcdefghijklmnopqrstuvwxyz0123456789")
}
