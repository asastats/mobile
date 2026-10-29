import XCTest
@testable import NativeSignInPlugin

final class NativeSignInRequestTests: XCTestCase {
    let nonce = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJ0123-_6"
    let web = "1054116980925-bje7a3i2vbttilei8re269n9q4lu42kk.apps.googleusercontent.com"
    let ios = "1054116980925-ev23pc8lk1vpsnvfa2ohfd4u9467skcr.apps.googleusercontent.com"

    func testProvidersMatchTheServer() {
        XCTAssertEqual(NativeSignInRequest.providers, ["apple", "google"])
    }

    func testAppleNeedsNoClientIds() {
        let request = NativeSignInRequest(provider: "apple", nonce: nonce, serverClientId: nil, iosClientId: nil)
        XCTAssertEqual(request?.provider, "apple")
        XCTAssertEqual(request?.nonce, nonce)
    }

    func testGoogleKeepsBothClientIds() {
        let request = NativeSignInRequest(provider: "google", nonce: nonce, serverClientId: web, iosClientId: ios)
        XCTAssertEqual(request?.serverClientId, web)
        XCTAssertEqual(request?.iosClientId, ios)
    }

    func testRefusesUnknownProviderAndBadNonce() {
        XCTAssertNil(NativeSignInRequest(provider: "github", nonce: nonce, serverClientId: nil, iosClientId: nil))
        XCTAssertNil(NativeSignInRequest(provider: nil, nonce: nonce, serverClientId: nil, iosClientId: nil))
        XCTAssertNil(NativeSignInRequest(provider: "apple", nonce: nil, serverClientId: nil, iosClientId: nil))
        XCTAssertNil(NativeSignInRequest(provider: "apple", nonce: "short", serverClientId: nil, iosClientId: nil))
        let bad = nonce.replacingOccurrences(of: "a", with: "=")
        XCTAssertNil(NativeSignInRequest(provider: "apple", nonce: bad, serverClientId: nil, iosClientId: nil))
    }

    func testGoogleRefusesMissingOrBadClientIds() {
        XCTAssertNil(NativeSignInRequest(provider: "google", nonce: nonce, serverClientId: nil, iosClientId: ios))
        XCTAssertNil(NativeSignInRequest(provider: "google", nonce: nonce, serverClientId: web, iosClientId: nil))
        for bad in ["evil.example.com", web + ".evil.com", "-abc.apps.googleusercontent.com",
                    "123-.apps.googleusercontent.com", "12a-abc.apps.googleusercontent.com",
                    "123-ABC.apps.googleusercontent.com", "1-2-3.apps.googleusercontent.com"] {
            XCTAssertNil(NativeSignInRequest(provider: "google", nonce: nonce, serverClientId: bad, iosClientId: ios), bad)
        }
    }

    func testHashedNonceIsHexSha256() {
        let request = NativeSignInRequest(provider: "apple", nonce: nonce, serverClientId: nil, iosClientId: nil)!
        XCTAssertEqual(request.hashedNonce.count, 64)
        let abc = String(repeating: "a", count: 43)
        XCTAssertEqual(
            NativeSignInRequest(provider: "apple", nonce: abc, serverClientId: nil, iosClientId: nil)!.hashedNonce,
            "66d34fba71f8f450f7e45598853e53bfc23bbd129027cbb131a2f4ffd7878cd0")
    }

    func testFailures() {
        XCTAssertEqual(NativeSignInRequest.failure(appleErrorCode: 1001), .cancelled)
        XCTAssertEqual(NativeSignInRequest.failure(appleErrorCode: 1000), .failed)
        XCTAssertEqual(NativeSignInRequest.failure(appleErrorCode: nil), .failed)
        XCTAssertEqual(NativeSignInRequest.failure(googleErrorCode: -5), .cancelled)
        XCTAssertEqual(NativeSignInRequest.failure(googleErrorCode: -4), .failed)
        XCTAssertEqual(NativeSignInFailure.unavailable.rawValue, "unavailable")
    }
}
