# Contributing

Thanks for helping. Bug reports with a small failing test are the most useful thing you can send.

## Run the tests

```bash
scripts/test.sh
```

It runs the tests of `scripts/ios-test`, which need no simulator, then the package's unit tests and
the UI tests of the app in `Example/`, through `scripts/ios-test`, on the newest iPhone simulator. Pass a simulator's id to pick another one. It also fails if the test runner restarted
or no test ran, which `xcodebuild` alone reports as success.
The full logs stay in `test-logs/`, and CI keeps them for a week as an artifact of each run.

## Make a change

1. Branch from `develop`. `main` holds releases only.
2. Add or change a test in `Example/StillwaterExampleUITests/`. Timing logic goes in
   `Tests/StillwaterTests/`, where it needs no simulator. A change to `scripts/ios-test` gets a test
   in `scripts/tests/`.
3. Add a line to `CHANGELOG.md` under Unreleased.
4. Open the pull request against `develop`.

## What belongs here

Stillwater holds what any app's UI tests need. A helper that knows about one app's screens, launch
arguments, or test data belongs in that app. New public API should say in its doc comment which
behavior of XCTest or iOS it works around.

## One thing to keep

`StillwaterCase` overrides `setUpWithError()`, not `setUp() async`. With the async one, every
failed assertion ends the test runner's process. The tests still look green, and only the log
shows it. `testAFailedAssertionLeavesTheRunnerAlive` and `scripts/test.sh` check this together.

## Release

1. On `release/<version>`, move Unreleased in `CHANGELOG.md` under the version.
2. Merge into `main` with `--no-ff`, and tag it `<version>`.
3. Merge `main` back into `develop`.

By contributing, you agree that your work is released under the [MIT License](LICENSE).
