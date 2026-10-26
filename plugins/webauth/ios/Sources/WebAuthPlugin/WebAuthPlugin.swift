import AuthenticationServices
import Capacitor
import UIKit

/// `WebAuth.start({provider, challenge, next})` → `{url}`; rejects with a
/// `WebAuthFailure` raw value. Design: capacitor/F4-DESIGN.md §9.
@objc(WebAuthPlugin)
public class WebAuthPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "WebAuthPlugin"
    public let jsName = "WebAuth"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "start", returnType: CAPPluginReturnPromise)
    ]

    private lazy var controller = WebAuthController(
        session: SystemAuthSession { [weak self] in self?.bridge?.viewController?.view.window })

    @objc func start(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            self.controller.start(
                server: self.bridge?.config.serverURL,
                provider: call.getString("provider"),
                challenge: call.getString("challenge"),
                next: call.getString("next")
            ) { result in
                switch result {
                case .success(let url):
                    call.resolve(["url": url.absoluteString])
                case .failure(let failure):
                    call.reject(failure.rawValue)
                }
            }
        }
    }
}

/// `ASWebAuthenticationSession` with an https callback, which iOS hands only to
/// an app the domain's `webcredentials` names (iOS 17.4+).
final class SystemAuthSession: NSObject, AuthSessionStarting,
    ASWebAuthenticationPresentationContextProviding {
    private let anchor: () -> UIWindow?
    private var session: ASWebAuthenticationSession?

    init(anchor: @escaping () -> UIWindow?) {
        self.anchor = anchor
    }

    func start(
        url: URL, callbackHost: String, callbackPath: String,
        completion: @escaping (Result<URL, WebAuthFailure>) -> Void
    ) -> Bool {
        guard #available(iOS 17.4, *) else { return false }

        let session = ASWebAuthenticationSession(
            url: url, callback: .https(host: callbackHost, path: callbackPath)
        ) { [weak self] callbackURL, error in
            self?.session = nil
            if let callbackURL = callbackURL {
                completion(.success(callbackURL))
            } else if (error as? ASWebAuthenticationSessionError)?.code == .canceledLogin {
                completion(.failure(.cancelled))
            } else {
                completion(.failure(.failed))
            }
        }
        session.prefersEphemeralWebBrowserSession = true
        session.presentationContextProvider = self
        self.session = session
        if !session.start() {
            self.session = nil
            completion(.failure(.failed))
        }
        return true
    }

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        anchor() ?? ASPresentationAnchor()
    }
}
