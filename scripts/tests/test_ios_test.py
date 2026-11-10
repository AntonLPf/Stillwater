"""Tests for scripts/ios-test. xcrun and xcodebuild are stood in for, so no simulator runs.

    python3 scripts/tests/test_ios_test.py
"""

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "ios-test"

loader = importlib.machinery.SourceFileLoader("ios_test", str(SCRIPT))
ios_test = importlib.util.module_from_spec(importlib.util.spec_from_loader("ios_test", loader))
sys.modules["ios_test"] = ios_test
loader.exec_module(ios_test)

IOS_18 = "com.apple.CoreSimulator.SimRuntime.iOS-18-5"
IOS_26 = "com.apple.CoreSimulator.SimRuntime.iOS-26-2"
IOS_27 = "com.apple.CoreSimulator.SimRuntime.iOS-27-0"
IOS_27_1 = "com.apple.CoreSimulator.SimRuntime.iOS-27-1"

CORES = 10


def simulator(udid, name, state="Shutdown"):
    return {"udid": udid, "name": name, "state": state}


class Run:
    """What xcodebuild does on one simulator."""

    def __init__(self, status=0, log="", summary=None, passed=3):
        self.status = status
        self.log = log
        self.summary = summary if summary is not None else {"passedTests": passed}


class Tools:
    """Stands in for xcrun and xcodebuild, and keeps the commands it was given, in order."""

    def __init__(self, devices):
        self.devices = devices
        self.commands = []
        self.settings = {}
        self.runs = {}
        self.summaries = {}
        self.build_status = 0
        self.build_log = ""
        self.unbootable = set()
        self.barrier = None
        self.up = {d["udid"] for ds in devices.values() for d in ds if d["state"] == "Booted"}
        self.most_up = len(self.up)
        self.lock = threading.Lock()

    def __call__(self, command, **options):
        with self.lock:
            self.commands.append(command)
        if command[0] == "xcodebuild":
            return self.xcodebuild(command, options["stdout"])
        if command[1] == "xcresulttool":
            return self.xcresulttool(command)
        return self.simctl(command)

    def done(self, command, status=0, stdout="", stderr=""):
        return subprocess.CompletedProcess(command, status, stdout, stderr)

    def simctl(self, command):
        action, rest = command[2], command[3:]
        if action == "list":
            return self.done(command, stdout=json.dumps({"devices": self.devices}))
        if action == "bootstatus":
            if rest[0] in self.unbootable:
                return self.done(command, 1, stderr="Unable to boot")
            with self.lock:
                self.up.add(rest[0])
                self.most_up = max(self.most_up, len(self.up))
            return self.done(command)
        if action == "shutdown":
            with self.lock:
                self.up.discard(rest[0])
            return self.done(command)
        if action == "ui":
            return self.ui(command, *rest)
        raise AssertionError(f"unexpected command: {command}")

    def ui(self, command, udid, setting, value=None):
        if value is None:
            current = self.settings.get((udid, setting), ios_test.DISPLAY_DEFAULTS[setting])
            return self.done(command, stdout=f"{current}\n")
        self.settings[udid, setting] = value
        return self.done(command)

    def xcresulttool(self, command):
        path = command[command.index("--path") + 1]
        if path not in self.summaries:
            return self.done(command, 1, stderr="No such bundle")
        return self.done(command, stdout=json.dumps(self.summaries[path]))

    def xcodebuild(self, command, output):
        if "build-for-testing" in command:
            output.write(self.build_log)
            if self.build_status:
                output.write("error: it did not build\n")
            return self.done(command, self.build_status)
        udid = option(command, "-destination").removeprefix("id=")
        if udid not in self.up:
            raise AssertionError(f"tests ran on {udid}, which is down")
        if "-test-iterations" in command and option(command, "-test-iterations") == "1":
            raise AssertionError("xcodebuild refuses one iteration")
        if self.barrier:
            self.barrier.wait(timeout=5)
        run = self.runs.get(udid, Run())
        output.write(run.log)
        path = option(command, "-resultBundlePath")
        Path(path).mkdir()  # xcodebuild refuses a path that exists.
        self.summaries[path] = run.summary
        return self.done(command, run.status)


def option(command, name):
    return command[command.index(name) + 1]


class IosTestCase(unittest.TestCase):
    config = "PROJECT=App.xcodeproj\nSCHEME=App\nUI_TESTS=AppUITests\nUNIT_TESTS=AppTests\n"
    devices = {
        IOS_18: [simulator("phone-18", "iPhone 16")],
        IOS_26: [simulator("mini-26", "iPad mini (A17 Pro)")],
        IOS_27: [
            simulator("phone-27", "iPhone 17", "Booted"),
            simulator("mini-27", "iPad mini (A17 Pro)"),
            simulator("air-27", "iPad Air 13-inch (M4)"),
        ],
        IOS_27_1: [simulator("duo", "iPhone Duo")],
    }

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(folder.name)
        Path(".ios-test").write_text(self.config)

        self.tools = Tools(json.loads(json.dumps(self.devices)))
        self.clock = 0
        self.loads = [1]
        for patch in (
            mock.patch("subprocess.run", self.tools),
            mock.patch("time.sleep", self.sleep),
            mock.patch("time.monotonic", lambda: self.clock),
            mock.patch("os.getloadavg", lambda: (self.next_load(), 0, 0)),
            mock.patch("os.cpu_count", lambda: CORES),
            mock.patch.dict(os.environ),
        ):
            patch.start()
            self.addCleanup(patch.stop)
        os.environ.pop("CI", None)

    def shut_down_the_iphone(self):
        self.tools.devices[IOS_27][0]["state"] = "Shutdown"
        self.tools.up.clear()
        self.tools.most_up = 0

    def sleep(self, seconds):
        self.clock += seconds
        self.tools.commands.append(["sleep", seconds])
        if self.clock > 3600:
            raise AssertionError("still waiting after an hour")

    def next_load(self):
        return self.loads.pop(0) if len(self.loads) > 1 else self.loads[0]

    def ios_test(self, *arguments):
        """Runs the command. Returns its exit code and everything it printed."""
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["ios-test", *arguments]):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                try:
                    code = ios_test.main()
                except SystemExit as exit:
                    code = exit.code
        return code, output.getvalue()

    @property
    def test_runs(self):
        return [c for c in self.tools.commands if "test-without-building" in c]

    @property
    def tested(self):
        return [option(c, "-destination").removeprefix("id=") for c in self.test_runs]

    def position(self, *command):
        """Where a command that starts with these words came, among all the commands."""
        for index, seen in enumerate(self.tools.commands):
            if seen[:len(command)] == list(command):
                return index
        self.fail(f"{command} never ran")

    def last_test_on(self, udid):
        return max(
            index for index, command in enumerate(self.tools.commands)
            if f"id={udid}" in command and "test-without-building" in command
        )


class ChoosingSimulators(IosTestCase):
    def test_quick_runs_the_newest_plain_iphone(self):
        self.ios_test("quick")
        self.assertEqual(self.tested, ["phone-27"])

    def test_close_runs_an_iphone_and_an_ipad_mini_on_the_newest_ios_with_both(self):
        self.ios_test("close")
        self.assertEqual(set(self.tested), {"phone-27", "mini-27"})

    def test_close_runs_no_ipad_for_an_iphone_only_app(self):
        Path(".ios-test").write_text(self.config + "DEVICES=iphone\n")
        self.ios_test("close")
        self.assertEqual(set(self.tested), {"phone-27"})

    def test_release_adds_the_named_simulators(self):
        Path(".ios-test").write_text(
            self.config + "RELEASE_SIMULATORS=iPhone Duo, iPad mini (A17 Pro)@26, iPhone 16@18\n"
        )
        self.ios_test("release")
        self.assertEqual(set(self.tested), {"phone-27", "mini-27", "duo", "mini-26", "phone-18"})

    def test_release_fails_on_a_simulator_that_is_not_there(self):
        Path(".ios-test").write_text(self.config + "RELEASE_SIMULATORS=iPhone 99\n")
        code, output = self.ios_test("release")
        self.assertEqual(code, 2)
        self.assertIn("no simulator matches 'iPhone 99'", output)
        self.assertEqual(self.test_runs, [])

    def test_an_id_picks_that_simulator(self):
        self.ios_test("quick", "--simulator", "air-27")
        self.assertEqual(self.tested, ["air-27"])


class Settling(IosTestCase):
    def test_a_simulator_that_was_down_settles_before_its_tests(self):
        self.loads = [50, 30, CORES]
        _, output = self.ios_test("quick", "--simulator", "mini-27")

        self.assertIn("Letting iPad mini (A17 Pro) (iOS 27.0) settle", output)
        sleeps = [c[1] for c in self.tools.commands if c[0] == "sleep"]
        self.assertEqual(sleeps, [60, 5, 5])
        self.assertLess(self.tools.commands.index(["sleep", 60]), self.last_test_on("mini-27"))
        self.assertLess(
            self.position("xcrun", "simctl", "bootstatus"), self.tools.commands.index(["sleep", 60])
        )

    def test_a_simulator_already_up_starts_at_once(self):
        _, output = self.ios_test("quick", "--simulator", "phone-27")
        self.assertNotIn("settle", output)
        self.assertFalse([c for c in self.tools.commands if c[0] == "sleep"])

    def test_ci_does_not_wait(self):
        os.environ["CI"] = "true"
        _, output = self.ios_test("quick", "--simulator", "mini-27")
        self.assertNotIn("settle", output)
        self.assertEqual(self.tested, ["mini-27"])

    def test_a_busy_mac_ends_the_wait_at_the_limit_and_the_tests_still_run(self):
        self.loads = [CORES + 1]
        code, output = self.ios_test("quick", "--simulator", "mini-27")
        self.assertIn(f"still busy after {ios_test.SETTLE_MINUTES} minutes", output)
        self.assertEqual(self.tested, ["mini-27"])
        self.assertEqual(code, 0)

    def test_a_second_simulator_boots_after_the_first_has_settled(self):
        self.shut_down_the_iphone()
        self.ios_test("close")

        commands = self.tools.commands
        boots = [i for i, c in enumerate(commands) if c[:3] == ["xcrun", "simctl", "bootstatus"]]
        sleeps = [i for i, c in enumerate(commands) if c == ["sleep", 60]]
        self.assertEqual(len(sleeps), 2)
        self.assertLess(boots[0], sleeps[0])
        self.assertLess(sleeps[0], boots[1])
        self.assertLess(boots[1], sleeps[1])
        self.assertLess(sleeps[1], min(commands.index(c) for c in self.test_runs))


class DisplaySettings(IosTestCase):
    def test_settings_left_behind_go_back_to_the_defaults(self):
        self.tools.settings["phone-27", "content_size"] = "extra-extra-large"
        self.tools.settings["phone-27", "appearance"] = "dark"
        self.tools.settings["phone-27", "increase_contrast"] = "enabled"

        _, output = self.ios_test("quick")

        self.assertIn("content_size was extra-extra-large, now large", output)
        self.assertEqual(self.tools.settings["phone-27", "content_size"], "large")
        self.assertEqual(self.tools.settings["phone-27", "appearance"], "light")
        self.assertEqual(self.tools.settings["phone-27", "increase_contrast"], "disabled")
        self.assertLess(
            self.position("xcrun", "simctl", "ui", "phone-27", "content_size", "large"),
            self.last_test_on("phone-27"),
        )

    def test_settings_at_their_defaults_are_left_alone(self):
        _, output = self.ios_test("quick")
        self.assertNotIn(" was ", output)
        changes = [c for c in self.tools.commands if c[:3] == ["xcrun", "simctl", "ui"] and c[5:]]
        self.assertEqual(changes, [])

    def test_a_setting_the_system_does_not_have_is_left_alone(self):
        self.tools.settings["phone-27", "increase_contrast"] = "unsupported"
        _, output = self.ios_test("quick")
        self.assertNotIn("increase_contrast", output)
        self.assertEqual(self.tools.settings["phone-27", "increase_contrast"], "unsupported")

    def test_a_simulator_that_cannot_boot_stops_the_run(self):
        self.tools.unbootable.add("mini-27")
        code, output = self.ios_test("quick", "--simulator", "mini-27")
        self.assertEqual(code, 2)
        self.assertIn("could not boot", output)
        self.assertEqual(self.test_runs, [])


class Pairs(IosTestCase):
    def setUp(self):
        super().setUp()
        Path(".ios-test").write_text(
            self.config + "RELEASE_SIMULATORS=iPad mini (A17 Pro)@26, iPhone 16@18\n"
        )

    def test_a_pair_runs_side_by_side(self):
        # Each run waits here for the other, so a run alone would time out and fail the test.
        self.tools.barrier = threading.Barrier(2)
        self.assertEqual(self.ios_test("close")[0], 0)

    def test_the_next_pair_starts_when_the_first_has_finished(self):
        self.ios_test("release")

        first_ended = max(self.last_test_on("phone-27"), self.last_test_on("mini-27"))
        boots = [
            c[3] for c in self.tools.commands[first_ended:]
            if c[:3] == ["xcrun", "simctl", "bootstatus"]
        ]
        self.assertEqual(set(boots), {"mini-26", "phone-18"})

    def test_a_pair_the_run_booted_shuts_down_before_the_next(self):
        self.ios_test("release")

        self.assertLess(
            self.position("xcrun", "simctl", "shutdown", "mini-27"),
            self.position("xcrun", "simctl", "bootstatus", "mini-26"),
        )

    def test_a_simulator_that_was_up_stays_up(self):
        self.ios_test("release")
        self.assertIn("phone-27", self.tools.up)

    def test_the_last_pair_stays_up_for_the_next_run(self):
        self.ios_test("release")
        self.assertLessEqual({"mini-26", "phone-18"}, self.tools.up)
        self.assertEqual(self.ios_test("close")[0], 0)

    def test_no_more_than_two_simulators_this_run_booted_are_up_at_once(self):
        self.shut_down_the_iphone()
        self.ios_test("release")
        self.assertEqual(self.tools.most_up, 2)


class Commands(IosTestCase):
    def test_quick_runs_the_ui_tests(self):
        self.ios_test("quick")
        self.assertEqual([option(c, "-scheme") for c in self.test_runs], ["App"])
        self.assertIn("-only-testing:AppUITests", self.test_runs[0])

    def test_quick_runs_the_unit_tests_if_there_are_no_ui_tests(self):
        Path(".ios-test").write_text("SCHEME=App\nUNIT_TESTS=AppTests\n")
        self.ios_test("quick")
        self.assertIn("-only-testing:AppTests", self.test_runs[0])
        self.assertNotIn("-project", self.test_runs[0])

    def test_close_runs_ui_tests_then_unit_tests_on_each_simulator(self):
        self.ios_test("close")
        targets = [[a for a in c if a.startswith("-only-testing")][0] for c in self.test_runs]
        self.assertEqual(targets, ["-only-testing:AppUITests"] * 2 + ["-only-testing:AppTests"] * 2)

    def test_each_run_has_its_own_result_bundle(self):
        self.ios_test("close")
        bundles = [option(c, "-resultBundlePath") for c in self.test_runs]
        self.assertEqual(len(set(bundles)), 4)

    def test_a_new_run_replaces_the_bundle_of_the_last(self):
        self.assertEqual(self.ios_test("quick")[0], 0)
        self.assertEqual(self.ios_test("quick")[0], 0)

    def test_no_run_uses_cloned_simulators(self):
        self.ios_test("close")
        for command in self.test_runs:
            self.assertEqual(option(command, "-parallel-testing-enabled"), "NO")

    def test_only_can_repeat_and_goes_to_the_right_suite(self):
        self.ios_test(
            "quick", "--only", "AppUITests/A/one", "--only", "AppUITests/A/two",
            "--only", "AppTests/B/three",
        )
        ui, unit = self.test_runs
        self.assertIn("-only-testing:AppUITests/A/one", ui)
        self.assertIn("-only-testing:AppUITests/A/two", ui)
        self.assertNotIn("-only-testing:AppTests/B/three", ui)
        self.assertIn("-only-testing:AppTests/B/three", unit)

    def test_iterations_repeat_the_tests(self):
        self.ios_test("quick", "--iterations", "3")
        self.assertEqual(option(self.test_runs[0], "-test-iterations"), "3")

    def test_one_iteration_is_left_out(self):
        self.ios_test("quick", "--iterations", "1")
        self.assertNotIn("-test-iterations", self.test_runs[0])

    def test_test_args_reach_xcodebuild(self):
        Path(".ios-test").write_text(self.config + "TEST_ARGS=-testLanguage en -testRegion US\n")
        self.ios_test("quick")
        self.assertEqual(option(self.test_runs[0], "-testLanguage"), "en")
        self.assertEqual(option(self.test_runs[0], "-testRegion"), "US")

    def test_a_failed_build_stops_the_run(self):
        self.tools.build_status = 65
        code, output = self.ios_test("quick")
        self.assertEqual(code, 2)
        self.assertIn("the build failed", output)
        self.assertEqual(self.test_runs, [])


class Report(IosTestCase):
    def row(self, output, passed, failed, skipped, outcome):
        pattern = rf"ui +iPhone 17 \(iOS 27\.0\) +{passed} +{failed} +{skipped}  {outcome}$"
        return re.search(pattern, output, re.MULTILINE)

    def report(self, run):
        self.tools.runs["phone-27"] = run
        return self.ios_test("quick")

    def test_a_run_that_passes(self):
        code, output = self.report(Run(summary={"passedTests": 5, "skippedTests": 2}))
        self.assertEqual(code, 0)
        self.assertTrue(self.row(output, 5, 0, 2, "ok"), output)

    def test_counts_come_from_the_bundle_not_the_log(self):
        log = "Test case 'A/parameterized(_:)' passed on 'iPhone 17' (0.1 seconds)\n" * 5
        _, output = self.report(Run(log=log, passed=1))
        self.assertTrue(self.row(output, 1, 0, 0, "ok"), output)

    def test_an_expected_failure_counts_as_passed(self):
        _, output = self.report(Run(summary={"passedTests": 11, "expectedFailures": 1}))
        self.assertTrue(self.row(output, 12, 0, 0, "ok"), output)

    def test_a_failed_test_reads_failed(self):
        code, output = self.report(Run(65, summary={"passedTests": 2, "failedTests": 1}))
        self.assertEqual(code, 1)
        self.assertTrue(self.row(output, 2, 1, 0, "FAILED"), output)
        self.assertNotIn("xcodebuild failed", output)
        self.assertIn("full log: test-logs/ui-iPhone-17-27.0.log", output)

    def test_failures_are_listed_with_their_class_on_one_line(self):
        failure = {
            "testName": "testA()",
            "testIdentifierString": "Case/testA()",
            "failureText": "Expectation failed\nvalue → 2",
        }
        _, output = self.report(Run(65, summary={"failedTests": 1, "testFailures": [failure]}))
        self.assertIn("  Case/testA(): Expectation failed value → 2\n", output)

    def test_a_failure_is_listed_once_however_many_iterations_it_failed(self):
        failure = {"testName": "testA()", "failureText": "failed"}
        _, output = self.report(Run(65, summary={"failedTests": 1, "testFailures": [failure] * 3}))
        self.assertEqual(output.count("testA(): failed"), 1)

    def test_xcodebuild_failing_with_no_failed_test_says_so(self):
        code, output = self.report(Run(70, summary={}))
        self.assertEqual(code, 1)
        self.assertTrue(self.row(output, 0, 0, 0, "xcodebuild failed"), output)

    def test_a_restarted_runner_fails_a_green_run(self):
        code, output = self.report(Run(log="Restarting after unexpected exit\n"))
        self.assertEqual(code, 1)
        self.assertIn("the test runner restarted", output)

    def test_no_test_fails_a_green_run(self):
        code, output = self.report(Run(summary={}))
        self.assertEqual(code, 1)
        self.assertIn("no test ran", output)

    def test_a_clone_fails_a_green_run(self):
        code, output = self.report(Run(log="passed on 'Clone 1 of iPhone 17'\n"))
        self.assertEqual(code, 1)
        self.assertIn("tests ran on cloned simulators", output)

    def test_one_bad_simulator_fails_the_whole_run(self):
        self.tools.runs["mini-27"] = Run(65, summary={"failedTests": 1})
        code, output = self.ios_test("close")
        self.assertEqual(code, 1)
        self.assertIn("FAILED", output)
        self.assertIn(" ok\n", output)


class Warnings(IosTestCase):
    def warning(self, path, message="'id' is main actor-isolated", place=":12:5"):
        return f"{Path.cwd()}/{path}{place}: warning: {message}\n"

    def build_with(self, *lines):
        self.tools.build_log = "".join(lines)

    @property
    def builds(self):
        return [c for c in self.tools.commands if "build-for-testing" in c]

    def test_quick_builds_what_changed_and_close_builds_from_clean(self):
        self.ios_test("quick")
        self.ios_test("close")
        self.ios_test("release")
        self.assertEqual(["clean" in c for c in self.builds], [False, True, True])

    def test_quick_lists_a_warning_and_passes(self):
        self.build_with(self.warning("App/Work.swift"))
        code, output = self.ios_test("quick")
        self.assertEqual(code, 0)
        self.assertIn("1 warning in the build:\n  App/Work.swift:12:5: 'id' is main actor-isolated\n", output)
        self.assertNotIn("allows none", output)

    def test_close_fails_on_a_warning_after_running_the_tests(self):
        self.build_with(self.warning("App/Work.swift"))
        code, output = self.ios_test("close")
        self.assertEqual(code, 1)
        self.assertEqual(len(self.test_runs), 4)
        self.assertIn("The build has 1 warning, and close allows none.", output)

    def test_release_fails_on_a_warning(self):
        self.build_with(self.warning("App/Work.swift"))
        code, output = self.ios_test("release")
        self.assertEqual(code, 1)
        self.assertIn("release allows none", output)

    def test_close_passes_a_build_without_warnings(self):
        self.build_with("Build settings from command line:\n", "** TEST BUILD SUCCEEDED **\n")
        code, output = self.ios_test("close")
        self.assertEqual(code, 0)
        self.assertNotIn("warning", output)

    def test_a_warning_printed_twice_counts_once(self):
        self.build_with(self.warning("App/Work.swift"), "  12 | let id = work.id\n", self.warning("App/Work.swift"))
        _, output = self.ios_test("close")
        self.assertIn("The build has 1 warning,", output)

    def test_two_warnings_on_one_line_count_twice(self):
        self.build_with(self.warning("App/Sort.swift", place=":88:32"), self.warning("App/Sort.swift", place=":88:41"))
        _, output = self.ios_test("close")
        self.assertIn("The build has 2 warnings,", output)

    def test_a_warning_inside_a_macro_names_the_line_it_came_from(self):
        self.build_with(
            "macro expansion #expect:1:63: warning: cannot form key path to 'id'\n",
            f"`- {Path.cwd()}/AppTests/WorkTests.swift:213:85: note: expanded code originates here\n",
            "213 |         #expect(works.map(\\.id) == [\"dune\"])\n",
        )
        _, output = self.ios_test("quick")
        self.assertIn("  AppTests/WorkTests.swift:213:85: cannot form key path to 'id'\n", output)

    def test_a_warning_about_a_whole_file_has_no_line(self):
        self.build_with(self.warning("App/Assets.xcassets", "an unassigned child", place=""))
        _, output = self.ios_test("quick")
        self.assertIn("  App/Assets.xcassets: an unassigned child\n", output)

    def test_a_package_built_outside_the_project_is_left_out(self):
        self.build_with(
            "/Users/me/Library/Developer/Xcode/DerivedData/App/SourcePackages/checkouts/Kit/Kit.swift:3:1: warning: old\n",
            "2026-11-10 21:17:02.420 appintentsmetadataprocessor[1:2] warning: Metadata extraction skipped\n",
        )
        code, output = self.ios_test("close")
        self.assertEqual(code, 0)
        self.assertNotIn("warning", output)

    def test_a_long_list_names_the_log_for_the_rest(self):
        self.build_with(*(self.warning(f"App/File{n:02}.swift") for n in range(25)))
        _, output = self.ios_test("quick")
        self.assertIn("25 warnings in the build:", output)
        self.assertIn("  App/File19.swift:12:5:", output)
        self.assertNotIn("App/File20.swift", output)
        self.assertIn("  and 5 more in test-logs/build-App.log", output)


if __name__ == "__main__":
    unittest.main()
