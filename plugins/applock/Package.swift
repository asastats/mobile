// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AsastatsApplock",
    platforms: [.iOS(.v15)],
    products: [
        .library(
            name: "AsastatsApplock",
            targets: ["AppLockPlugin"])
    ],
    dependencies: [
        .package(url: "https://github.com/ionic-team/capacitor-swift-pm.git", from: "8.0.0")
    ],
    targets: [
        .target(
            name: "AppLockPlugin",
            dependencies: [
                .product(name: "Capacitor", package: "capacitor-swift-pm"),
                .product(name: "Cordova", package: "capacitor-swift-pm")
            ],
            path: "ios/Sources/AppLockPlugin"),
        .testTarget(
            name: "AppLockPluginTests",
            dependencies: ["AppLockPlugin"],
            path: "ios/Tests/AppLockPluginTests")
    ]
)
