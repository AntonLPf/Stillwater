// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "Stillwater",
    platforms: [.iOS(.v18)],
    products: [
        .library(name: "Stillwater", targets: ["Stillwater"]),
    ],
    targets: [
        .target(
            name: "Stillwater",
            linkerSettings: [.linkedFramework("XCTest")]
        ),
        .testTarget(
            name: "StillwaterTests",
            dependencies: ["Stillwater"]
        ),
    ]
)
