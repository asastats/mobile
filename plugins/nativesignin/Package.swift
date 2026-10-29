// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AsastatsNativesignin",
    platforms: [.iOS(.v15)],
    products: [
        .library(
            name: "AsastatsNativesignin",
            targets: ["NativeSignInPlugin"])
    ],
    dependencies: [
        .package(url: "https://github.com/ionic-team/capacitor-swift-pm.git", from: "8.0.0"),
        // The nonce argument of signIn(withPresenting:...) arrived in 9.0.0; see docs/logbook.md.
        .package(url: "https://github.com/google/GoogleSignIn-iOS.git", "9.2.0"..<"11.0.0")
    ],
    targets: [
        .target(
            name: "NativeSignInPlugin",
            dependencies: [
                .product(name: "Capacitor", package: "capacitor-swift-pm"),
                .product(name: "Cordova", package: "capacitor-swift-pm"),
                .product(name: "GoogleSignIn", package: "GoogleSignIn-iOS")
            ],
            path: "ios/Sources/NativeSignInPlugin"),
        .testTarget(
            name: "NativeSignInPluginTests",
            dependencies: ["NativeSignInPlugin"],
            path: "ios/Tests/NativeSignInPluginTests")
    ]
)
