import Capacitor
import Foundation

/// Reads what the old Flutter app saved under the same bundle id (docs/logbook.md).
@objc(FlutterDataPlugin)
public class FlutterDataPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "FlutterDataPlugin"
    public let jsName = "FlutterData"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "readAddresses", returnType: CAPPluginReturnPromise)
    ]

    @objc func readAddresses(_ call: CAPPluginCall) {
        call.resolve(["addresses": FlutterAddresses.read(from: .standard)])
    }
}
