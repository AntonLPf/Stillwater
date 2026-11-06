import SwiftUI

/// A small screen with the things UI tests trip over: rows that come late, a sheet that
/// slides, and a keyboard.
struct ContentView: View {
    @State private var showsLateRow = false
    @State private var showsSheet = false
    @State private var name = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Timing") {
                    Button("Show Late Row") {
                        Task {
                            try? await Task.sleep(for: .milliseconds(500))
                            showsLateRow = true
                        }
                    }
                    .accessibilityIdentifier("home.showLateRow")

                    Button("Hide Late Row") {
                        Task {
                            try? await Task.sleep(for: .milliseconds(500))
                            showsLateRow = false
                        }
                    }
                    .accessibilityIdentifier("home.hideLateRow")

                    if showsLateRow {
                        Text("Late Row")
                            .accessibilityIdentifier("home.lateRow")
                    }
                }

                Section("Motion") {
                    Button("Open Sheet") {
                        showsSheet = true
                    }
                    .accessibilityIdentifier("home.openSheet")
                }

                Section("Keyboard") {
                    TextField("Name", text: $name)
                        .accessibilityIdentifier("home.name")
                    Text(name.isEmpty ? "No name" : "Hello, \(name)")
                        .accessibilityIdentifier("home.greeting")
                }
            }
            .navigationTitle("Stillwater")
        }
        .sheet(isPresented: $showsSheet) {
            VStack(spacing: 16) {
                Text("A sheet that slides in")
                Button("Close") {
                    showsSheet = false
                }
                .accessibilityIdentifier("sheet.close")
            }
            .padding()
            .presentationDetents([.medium])
        }
    }
}

#Preview {
    ContentView()
}
