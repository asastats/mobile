import XCTest
@testable import FlutterDataPlugin

final class FlutterAddressesTests: XCTestCase {
    private var defaults: UserDefaults!
    private let suite = "FlutterAddressesTests"

    override func setUp() {
        super.setUp()
        defaults = UserDefaults(suiteName: suite)
        defaults.removePersistentDomain(forName: suite)
    }

    override func tearDown() {
        defaults.removePersistentDomain(forName: suite)
        super.tearDown()
    }

    func testMissingKeyIsEmpty() {
        XCTAssertEqual(FlutterAddresses.read(from: defaults), [])
    }

    func testReadsTheStringArrayInOrder() {
        defaults.set(["b.algo", "a.algo"], forKey: "flutter.address")
        XCTAssertEqual(FlutterAddresses.read(from: defaults), ["b.algo", "a.algo"])
    }

    func testKeepsOnlyStrings() {
        defaults.set(["a.algo", 7, "b.algo"] as [Any], forKey: "flutter.address")
        XCTAssertEqual(FlutterAddresses.read(from: defaults), ["a.algo", "b.algo"])
    }

    func testAStringValueIsEmpty() {
        defaults.set("a.algo", forKey: "flutter.address")
        XCTAssertEqual(FlutterAddresses.read(from: defaults), [])
    }
}
