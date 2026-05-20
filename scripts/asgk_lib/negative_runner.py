from __future__ import annotations

import contextlib
import io
import shlex
import subprocess

from asgk_lib.common import ROOT
from asgk_lib.negative_cases import (
    COMMANDS_PASS,
    EXPECTED_FAILURE,
    EXPECTED_SUCCESS,
    NEGATIVE_CASE_CHOICES,
    NEGATIVE_CASE_GROUPS,
    NegativeCaseGroup,
)


def format_command(args: tuple[str, ...]) -> str:
    return shlex.join(args)


def run_captured(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def print_captured_output(output: str) -> None:
    if output.strip():
        print(output.rstrip())


def run_many(commands: tuple[tuple[str, ...], ...]) -> int:
    failures: list[tuple[tuple[str, ...], str]] = []
    for command in commands:
        result = run_captured(command)
        if result.returncode != 0:
            failures.append((command, result.stdout))
    if failures:
        for command, output in failures:
            print(f"FAIL: command failed: {format_command(command)}")
            print_captured_output(output)
        print(f"FAIL: {len(failures)} command(s) failed.")
        return 1
    print(f"Checks passed: {len(commands)} command(s).")
    return 0


def run_expected_failures(commands: tuple[tuple[str, ...], ...]) -> int:
    unexpected_passes: list[tuple[tuple[str, ...], str]] = []
    for command in commands:
        result = run_captured(command)
        if result.returncode == 0:
            unexpected_passes.append((command, result.stdout))
    if unexpected_passes:
        for command, output in unexpected_passes:
            print(f"FAIL: expected command to fail, but it passed: {format_command(command)}")
            print_captured_output(output)
        print(f"FAIL: {len(unexpected_passes)} expected-failure check(s) unexpectedly passed.")
        return 1
    print(f"Expected-failure checks passed: {len(commands)} command(s) failed as expected.")
    return 0


def run_expected_successes(commands: tuple[tuple[str, ...], ...]) -> int:
    failures: list[tuple[tuple[str, ...], str]] = []
    for command in commands:
        result = run_captured(command)
        if result.returncode != 0:
            failures.append((command, result.stdout))
    if failures:
        for command, output in failures:
            print(f"FAIL: expected command to pass, but it failed: {format_command(command)}")
            print_captured_output(output)
        print(f"FAIL: {len(failures)} expected-success check(s) failed.")
        return 1
    print(f"Expected-success checks passed: {len(commands)} command(s) passed as expected.")
    return 0


def run_case_group(group: NegativeCaseGroup) -> int:
    if group.mode == COMMANDS_PASS:
        return run_many(group.commands)
    if group.mode == EXPECTED_FAILURE:
        return run_expected_failures(group.commands)
    if group.mode == EXPECTED_SUCCESS:
        return run_expected_successes(group.commands)
    print(f"FAIL: unsupported negative case mode: {group.mode}")
    return 1


def run_negative_case_capture(case: str) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = run_negative_case(case)
    return result, buffer.getvalue()


def run_changed_path_hygiene_checks() -> int:
    return run_case_group(NEGATIVE_CASE_GROUPS["changed-paths"])


def run_textual_negative_checks() -> int:
    return run_case_group(NEGATIVE_CASE_GROUPS["textual"])


def run_negative_case(case: str) -> int:
    if case == "all":
        children = [child for child in NEGATIVE_CASE_CHOICES if child != "all"]
        failures: list[tuple[str, str]] = []
        for child in children:
            result, output = run_negative_case_capture(child)
            if result != 0:
                failures.append((child, output))
        if failures:
            for child, output in failures:
                print(f"FAIL: negative case group failed: {child}")
                print_captured_output(output)
            print(f"FAIL: {len(failures)} negative case group(s) failed.")
            return 1
        print(f"Negative checks passed: {len(children)} group(s).")
        return 0

    group = NEGATIVE_CASE_GROUPS.get(case)
    if group is None:
        print(f"FAIL: unsupported negative case group: {case}")
        return 1
    return run_case_group(group)
