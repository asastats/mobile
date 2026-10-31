// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AsastatsFlutterdata",
    platforms: [.iOS(.v15)],
    products: [
        .library(
            name: "AsastatsFlutterdata",
            targets: ["FlutterDataPlugin"])
    ],
    dependencies: [
        .package(url: "https://github.com/ionic-team/capacitor-swift-pm.git", from: "8.0.0")
    ],
    targets: [
        .target(
            name: "FlutterDataPlugin",
            dependencies: [
                .product(name: "Capacitor", package: "capacitor-swift-pm"),
                .product(name: "Cordova", package: "capacitor-swift-pm")
            ],
            path: "ios/Sources/FlutterDataPlugin"),
        .testTarget(
            name: "FlutterDataPluginTests",
            dependencies: ["FlutterDataPlugin"],
            path: "ios/Tests/FlutterDataPluginTests")
    ]
)
