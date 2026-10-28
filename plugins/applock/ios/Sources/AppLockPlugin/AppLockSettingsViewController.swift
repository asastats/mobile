import UIKit

/// The lock's own screen, opened by AppLock.openSettings(); each change asks first.
final class AppLockSettingsViewController: UIViewController {
    private let changed: (Bool) -> Void
    private let toggle = UISwitch()
    private let note = UILabel()

    /// - Parameter changed: called with the new setting after a successful prompt.
    init(changed: @escaping (Bool) -> Void) {
        self.changed = changed
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) is not used")
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "App lock"
        view.backgroundColor = .systemGroupedBackground
        navigationItem.rightBarButtonItem = UIBarButtonItem(
            barButtonSystemItem: .done, target: self, action: #selector(close))

        let label = UILabel()
        label.text = "Lock ASA Stats"
        label.font = .preferredFont(forTextStyle: .body)
        let row = UIStackView(arrangedSubviews: [label, toggle])
        row.axis = .horizontal
        note.numberOfLines = 0
        note.font = .preferredFont(forTextStyle: .footnote)
        note.textColor = .secondaryLabel
        let column = UIStackView(arrangedSubviews: [row, note])
        column.axis = .vertical
        column.spacing = 12
        column.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(column)
        NSLayoutConstraint.activate([
            column.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 20),
            column.leadingAnchor.constraint(equalTo: view.layoutMarginsGuide.leadingAnchor),
            column.trailingAnchor.constraint(equalTo: view.layoutMarginsGuide.trailingAnchor),
        ])
        toggle.addTarget(self, action: #selector(change), for: .valueChanged)
        refresh()
    }

    private func refresh() {
        let available = AppLockAuth.canAuthenticate
        if !available && AppLockAuth.enabled {
            AppLockAuth.enabled = false
            changed(false)
        }
        toggle.isEnabled = available
        toggle.isOn = AppLockAuth.enabled
        note.text = available
            ? "Asks for Face ID, Touch ID or your passcode when ASA Stats opens, and when you come back after more than a minute away."
            : "Set up Face ID, Touch ID or a passcode in Settings first."
    }

    /// The switch shows the saved state until the prompt succeeds.
    @objc private func change() {
        let on = toggle.isOn
        toggle.setOn(!on, animated: false)
        AppLockAuth.ask(reason: on ? "Turn on the app lock" : "Turn off the app lock") { [weak self] ok in
            guard ok, let self = self else { return }
            AppLockAuth.enabled = on
            self.toggle.setOn(on, animated: true)
            self.changed(on)
        }
    }

    @objc private func close() {
        dismiss(animated: true)
    }
}
