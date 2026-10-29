import UIKit
import Capacitor
import WebKit

class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
        guard let windowScene = scene as? UIWindowScene else { return }

        window = UIWindow(windowScene: windowScene)
        window?.rootViewController = AppViewController()
        window?.makeKeyAndVisible()

        SceneDelegateProxy.shared.scene(scene, willConnectTo: session, options: connectionOptions)
    }

    func scene(_ scene: UIScene, openURLContexts URLContexts: Set<UIOpenURLContext>) {
        SceneDelegateProxy.shared.scene(scene, openURLContexts: URLContexts)
    }

    func scene(_ scene: UIScene, continue userActivity: NSUserActivity) {
        SceneDelegateProxy.shared.scene(scene, continue: userActivity)
    }
}

/// Capacitor's controller, with offline.html told which page failed, for Retry (offline/offline.js).
final class AppViewController: CAPBridgeViewController {
    /// The web view keeps its navigation delegate weakly.
    private var offlineRetry: OfflineRetryDelegate?

    override func capacitorDidLoad() {
        super.capacitorDidLoad()
        guard let webView = webView, let inner = webView.navigationDelegate,
              let errorURL = bridge?.config.errorPathURL
        else { return }
        let delegate = OfflineRetryDelegate(inner: inner, errorURL: errorURL)
        offlineRetry = delegate
        webView.navigationDelegate = delegate
    }
}

/// Capacitor's navigation delegate with its two load-failure calls replaced: the same errorPath,
/// remembering the failed page, which `didFinish` hands to offline.html as
/// `window.ASASTATS_RETRY`. Everything else is forwarded unchanged.
final class OfflineRetryDelegate: NSObject, WKNavigationDelegate {
    private let inner: WKNavigationDelegate
    private let errorURL: URL
    private var failedPage: URL?

    init(inner: WKNavigationDelegate, errorURL: URL) {
        self.inner = inner
        self.errorURL = errorURL
    }

    override func responds(to aSelector: Selector!) -> Bool {
        super.responds(to: aSelector) || inner.responds(to: aSelector)
    }

    override func forwardingTarget(for aSelector: Selector!) -> Any? {
        inner.responds(to: aSelector) ? inner : nil
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        inner.webView?(webView, didFinish: navigation)
        guard let page = failedPage, webView.url?.absoluteString.hasPrefix(errorURL.absoluteString) == true
        else { return }
        webView.evaluateJavaScript(OfflineRetryDelegate.retryScript(page), completionHandler: nil)
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        showOffline(webView, error)
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        showOffline(webView, error)
    }

    private func showOffline(_ webView: WKWebView, _ error: Error) {
        let failed = (error as NSError).userInfo[NSURLErrorFailingURLErrorKey] as? URL
        // The error page's own failure keeps the earlier page and cannot loop.
        if let failed = failed, !failed.absoluteString.hasPrefix(errorURL.absoluteString) {
            failedPage = failed
        }
        webView.load(URLRequest(url: errorURL))
    }

    /// The URL as a JSON string literal, so nothing in it can end the statement.
    static func retryScript(_ page: URL) -> String {
        let data = (try? JSONSerialization.data(withJSONObject: [page.absoluteString])) ?? Data("[\"\"]".utf8)
        let array = String(data: data, encoding: .utf8) ?? "[\"\"]"
        return "window.ASASTATS_RETRY = \(array)[0];"
    }
}
