import Foundation

/// What the old Flutter app saved: shared_preferences keeps a string list as an array
/// in standard UserDefaults under its "flutter."-prefixed key (docs/logbook.md).
public enum FlutterAddresses {
    public static let key = "flutter.address"

    /// The stored strings, or none when the key is missing or holds anything else.
    public static func read(from defaults: UserDefaults) -> [String] {
        guard let items = defaults.array(forKey: key) else { return [] }
        return items.compactMap { $0 as? String }
    }
}
