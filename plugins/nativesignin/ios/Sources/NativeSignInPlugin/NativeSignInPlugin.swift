import AuthenticationServices
import Capacitor
import GoogleSignIn
import UIKit

/// `NativeSignIn.isAvailable({provider})` → `{available}`;
/// `NativeSignIn.signIn({provider, nonce, serverClientId})` →
/// `{idToken, authorizationCode?, givenName?, familyName?}`, rejecting with a
/// `NativeSignInFailure` raw value. Design: capacitor/O3-NATIVE-SIGNIN-DESIGN.md.
@objc(NativeSignInPlugin)
public class NativeSignInPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "NativeSignInPlugin"
    public let jsName = "NativeSignIn"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "isAvailable", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "signIn", returnType: CAPPluginReturnPromise)
    ]

    private var apple: AppleSignIn?
    private var busy = false

    override public func load() {
        NotificationCenter.default.addObserver(
            self, selector: #selector(openURL(_:)), name: .capacitorOpenURL, object: nil)
    }

    /// Google's SDK finishes some flows through the reversed-client-id URL scheme.
    @objc func openURL(_ notification: Notification) {
        guard let url = (notification.object as? [String: Any])?["url"] as? URL else { return }
        _ = GIDSignIn.sharedInstance.handle(url)
    }

    @objc func isAvailable(_ call: CAPPluginCall) {
        call.resolve(["available": NativeSignInRequest.providers.contains(call.getString("provider") ?? "")])
    }

    @objc func signIn(_ call: CAPPluginCall) {
        guard let request = NativeSignInRequest(
            provider: call.getString("provider"),
            nonce: call.getString("nonce"),
            serverClientId: call.getString("serverClientId"),
            // Also read by Google's SDK; set from capacitor/keys (O3 user step A4).
            iosClientId: Bundle.main.object(forInfoDictionaryKey: "GIDClientID") as? String)
        else {
            call.reject(NativeSignInFailure.invalid.rawValue)
            return
        }
        DispatchQueue.main.async {
            guard !self.busy else {
                call.reject(NativeSignInFailure.busy.rawValue)
                return
            }
            self.busy = true
            let finish: (Result<[String: Any], NativeSignInFailure>) -> Void = { result in
                self.busy = false
                self.apple = nil
                switch result {
                case .success(let values): call.resolve(values)
                case .failure(let failure): call.reject(failure.rawValue)
                }
            }
            if request.provider == "apple" {
                self.signInWithApple(request, finish)
            } else {
                self.signInWithGoogle(request, finish)
            }
        }
    }

    private func signInWithApple(
        _ request: NativeSignInRequest,
        _ finish: @escaping (Result<[String: Any], NativeSignInFailure>) -> Void
    ) {
        let apple = AppleSignIn(anchor: { [weak self] in self?.bridge?.viewController?.view.window },
                                completion: finish)
        self.apple = apple
        apple.start(hashedNonce: request.hashedNonce)
    }

    private func signInWithGoogle(
        _ request: NativeSignInRequest,
        _ finish: @escaping (Result<[String: Any], NativeSignInFailure>) -> Void
    ) {
        guard let presenter = bridge?.viewController,
              let clientID = request.iosClientId, let serverClientID = request.serverClientId
        else {
            finish(.failure(.failed))
            return
        }
        GIDSignIn.sharedInstance.configuration = GIDConfiguration(
            clientID: clientID, serverClientID: serverClientID)
        GIDSignIn.sharedInstance.signIn(
            withPresenting: presenter, hint: nil, additionalScopes: nil, nonce: request.nonce
        ) { result, error in
            if let error = error as NSError? {
                let code = error.domain == GIDSignInError.errorDomain ? error.code : nil
                finish(.failure(NativeSignInRequest.failure(googleErrorCode: code)))
                return
            }
            guard let user = result?.user, let token = user.idToken?.tokenString else {
                finish(.failure(.failed))
                return
            }
            var values: [String: Any] = ["idToken": token]
            values["givenName"] = user.profile?.givenName
            values["familyName"] = user.profile?.familyName
            // The app keeps no Google session: the server's is the one that counts.
            GIDSignIn.sharedInstance.signOut()
            finish(.success(values))
        }
    }
}

/// One Sign in with Apple sheet; the plugin keeps it alive until it answers.
final class AppleSignIn: NSObject, ASAuthorizationControllerDelegate,
    ASAuthorizationControllerPresentationContextProviding {
    private let anchor: () -> UIWindow?
    private let completion: (Result<[String: Any], NativeSignInFailure>) -> Void

    init(anchor: @escaping () -> UIWindow?,
         completion: @escaping (Result<[String: Any], NativeSignInFailure>) -> Void) {
        self.anchor = anchor
        self.completion = completion
    }

    func start(hashedNonce: String) {
        let request = ASAuthorizationAppleIDProvider().createRequest()
        request.requestedScopes = [.fullName, .email]
        request.nonce = hashedNonce
        let controller = ASAuthorizationController(authorizationRequests: [request])
        controller.delegate = self
        controller.presentationContextProvider = self
        controller.performRequests()
    }

    func authorizationController(
        controller: ASAuthorizationController,
        didCompleteWithAuthorization authorization: ASAuthorization
    ) {
        guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
              let tokenData = credential.identityToken,
              let token = String(data: tokenData, encoding: .utf8)
        else {
            completion(.failure(.failed))
            return
        }
        var values: [String: Any] = ["idToken": token]
        // Apple gives the name only on the first sign-in.
        values["authorizationCode"] = credential.authorizationCode.flatMap { String(data: $0, encoding: .utf8) }
        values["givenName"] = credential.fullName?.givenName
        values["familyName"] = credential.fullName?.familyName
        completion(.success(values))
    }

    func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        completion(.failure(NativeSignInRequest.failure(appleErrorCode: (error as? ASAuthorizationError)?.code.rawValue)))
    }

    func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
        anchor() ?? ASPresentationAnchor()
    }
}
