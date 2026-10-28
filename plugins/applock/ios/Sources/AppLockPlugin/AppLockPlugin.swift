import Capacitor
import LocalAuthentication
import UIKit

/// The lock is native: a cover over the WebView and the system prompt. Pages can only
/// `AppLock.openSettings()`. Design: capacitor/O2-BIOMETRIC-LOCK-DESIGN.md.
@objc(AppLockPlugin)
public class AppLockPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "AppLockPlugin"
    public let jsName = "AppLock"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "openSettings", returnType: CAPPluginReturnPromise)
    ]

    private var policy = LockPolicy(enabled: AppLockAuth.enabled)
    private lazy var cover = LockCover { [weak self] in self?.askIfLocked() }

    override public func load() {
        let center = NotificationCenter.default
        // didEnterBackground is before the app-switcher snapshot, so it shows the cover.
        center.addObserver(
            self, selector: #selector(didEnterBackground),
            name: UIApplication.didEnterBackgroundNotification, object: nil)
        center.addObserver(
            self, selector: #selector(didBecomeActive),
            name: UIApplication.didBecomeActiveNotification, object: nil)
        if policy.isLocked {
            DispatchQueue.main.async { self.showCover() }
        }
    }

    @objc func openSettings(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            let settings = AppLockSettingsViewController { [weak self] enabled in
                self?.policy.setEnabled(enabled)
            }
            self.bridge?.viewController?.present(
                UINavigationController(rootViewController: settings), animated: true)
            call.resolve()
        }
    }

    @objc private func didEnterBackground() {
        guard policy.isEnabled else { return }
        policy.background(now: ProcessInfo.processInfo.systemUptime)
        showCover()
    }

    @objc private func didBecomeActive() {
        switch policy.foreground(
            now: ProcessInfo.processInfo.systemUptime, canAuthenticate: AppLockAuth.canAuthenticate)
        {
        case .prompt:
            showCover()
            ask()
        case .disabled:
            AppLockAuth.enabled = false
            cover.removeFromSuperview()
        case .show:
            cover.removeFromSuperview()
        case .wait:
            break
        }
    }

    private func askIfLocked() {
        if policy.isLocked { ask() }
    }

    private func ask() {
        policy.authenticating()
        AppLockAuth.ask(reason: "Unlock ASA Stats") { [weak self] ok in
            guard let self = self else { return }
            self.policy.authenticated(ok)
            if ok { self.cover.removeFromSuperview() }
        }
    }

    private func showCover() {
        guard let view = bridge?.viewController?.view, cover.superview == nil else { return }
        cover.frame = view.bounds
        cover.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(cover)
    }
}

/// The saved setting and the system prompt, shared by the plugin and the settings screen.
enum AppLockAuth {
    private static let key = "asastats.applock.enabled"

    static var enabled: Bool {
        get { UserDefaults.standard.bool(forKey: key) }
        set { UserDefaults.standard.set(newValue, forKey: key) }
    }

    /// Face ID, Touch ID or the passcode: `.deviceOwnerAuthentication`, no key is unlocked.
    static var canAuthenticate: Bool {
        LAContext().canEvaluatePolicy(.deviceOwnerAuthentication, error: nil)
    }

    static func ask(reason: String, done: @escaping (Bool) -> Void) {
        LAContext().evaluatePolicy(.deviceOwnerAuthentication, localizedReason: reason) { ok, _ in
            DispatchQueue.main.async { done(ok) }
        }
    }
}

/// Full-screen cover in the splash colour, with an Unlock button.
final class LockCover: UIView {
    private let onUnlock: () -> Void

    init(onUnlock: @escaping () -> Void) {
        self.onUnlock = onUnlock
        super.init(frame: .zero)
        // capacitor.config.ts backgroundColor, #140a2e.
        backgroundColor = UIColor(red: 0x14 / 255, green: 0x0a / 255, blue: 0x2e / 255, alpha: 1)
        let button = UIButton(type: .system)
        button.setTitle("Unlock", for: .normal)
        button.titleLabel?.font = .preferredFont(forTextStyle: .title3)
        button.tintColor = .white
        button.addTarget(self, action: #selector(unlock), for: .touchUpInside)
        button.translatesAutoresizingMaskIntoConstraints = false
        addSubview(button)
        NSLayoutConstraint.activate([
            button.centerXAnchor.constraint(equalTo: centerXAnchor),
            button.centerYAnchor.constraint(equalTo: centerYAnchor),
        ])
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) is not used")
    }

    @objc private func unlock() {
        onUnlock()
    }
}
