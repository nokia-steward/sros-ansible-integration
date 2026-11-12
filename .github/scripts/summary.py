#!/usr/bin/env python3
# version: 1
# Copied from nokia-steward-validator pattern/. Do not edit: the linter checks this file is unchanged.
"""
Turn the JUnit XML of one case into a result row: passed, failed or skipped, counts and one line per failure.

GitHub Actions (.github/workflows/ci.yml) and nokia-steward-validator render results with this file, so
both show the same table.

  summary.py case --suite S --case LABEL --outcome success|failure|cancelled|skipped
                  [--setup-outcome success|failure] [--junit-dir tests/output/junit] [--experimental]

Standard library only.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field

VERSION = 1
DEFAULT_JUNIT_DIR = "tests/output/junit"
MESSAGE_LIMIT = 200
TIMEOUT_EXIT = 124
CANCELLED_EXIT = 130


@dataclass
class Result:
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped


@dataclass
class CaseResult:
    suite: str
    label: str
    status: str
    passed: int
    failed: int
    skipped: int
    message: str = ""
    experimental: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def first_line(text: str | None, limit: int = MESSAGE_LIMIT) -> str:
    for line in (text or "").splitlines():
        line = " ".join(line.split())
        if line:
            return line if len(line) <= limit else line[: limit - 3] + "..."
    return ""


def junit_files(directory: str = DEFAULT_JUNIT_DIR) -> list[str]:
    return sorted(glob.glob(os.path.join(directory, "**", "*.xml"), recursive=True))


def read_junit(paths: list[str]) -> Result:
    """Counts and failure messages of all testcases in the given JUnit XML files."""
    result = Result()
    for path in paths:
        try:
            root = ET.parse(path).getroot()  # noqa: S314  expat does not resolve external entities
        except (ET.ParseError, OSError) as e:
            result.failed += 1
            result.failures.append((os.path.basename(path), f"unreadable JUnit file: {e}"))
            continue
        for case in root.iter("testcase"):
            name = case.get("name") or case.get("classname") or "unnamed"
            problem = case.find("failure")
            if problem is None:
                problem = case.find("error")
            if problem is not None:
                result.failed += 1
                result.failures.append((name, first_line(problem.get("message")) or first_line(problem.text)))
            elif case.find("skipped") is not None:
                result.skipped += 1
            else:
                result.passed += 1
    return result


def evaluate(
    result: Result,
    suite: str,
    label: str,
    stage: str = "suite",
    exit_code: int = 0,
    timeout_minutes: int | None = None,
    experimental: bool = False,
) -> CaseResult:
    """The result of one case from its JUnit results and how its commands ended.

    stage is where it ended: 'prepare' (toolchains, packages, services), 'setup' ('make test-setup')
    or 'suite' (the suite command).
    """
    failed, message = result.failed, ""
    if result.failures:
        name, text = result.failures[0]
        message = first_line(f"{name}: {text}" if text else name)
    if stage == "prepare" and exit_code != 0:
        failed = max(failed, 1)
        message = "preparing the runner failed (toolchain, packages or services)"
    elif stage == "setup" and exit_code != 0:
        failed = max(failed, 1)
        message = f"make test-setup failed (exit code {exit_code})"
    elif exit_code in (TIMEOUT_EXIT, CANCELLED_EXIT):
        failed = max(failed, 1)
        if exit_code == TIMEOUT_EXIT:
            reason = "timed out" + (f" after {timeout_minutes} minutes" if timeout_minutes else "")
        else:
            reason = "cancelled (by hand or by the timeout)"
        message = reason + (f"; first failure: {message}" if message else "")
    elif exit_code != 0 and failed == 0:
        failed = 1
        message = f"suite command exited with {exit_code}" + ("" if result.total else ", no JUnit results")
    if failed:
        status = "failed"
    elif result.passed == 0 and result.skipped:
        status = "skipped"
        message = message or "all tests skipped"
    else:
        status = "passed"
        if not result.total:
            message = "no JUnit results, command succeeded"
    return CaseResult(suite, label, status, result.passed, failed, result.skipped, first_line(message), experimental)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_table(rows: list[CaseResult]) -> str:
    lines = ["| Suite | Case | Result | Passed / failed / skipped | Message |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        status = row.status + (" (experimental)" if row.experimental else "")
        counts = f"{row.passed} / {row.failed} / {row.skipped}"
        lines.append(f"| {_cell(row.suite)} | {_cell(row.label)} | {status} | {counts} | {_cell(row.message)} |")
    return "\n".join(lines) + "\n"


def totals(rows: list[CaseResult]) -> dict[str, int]:
    return {
        "passed": sum(r.status == "passed" for r in rows),
        "failed": sum(r.status == "failed" for r in rows),
        "skipped": sum(r.status == "skipped" for r in rows),
        "blocking_failures": sum(r.status == "failed" and not r.experimental for r in rows),
    }


def _outcome_exit(outcome: str) -> int:
    return {"success": 0, "skipped": 0, "cancelled": CANCELLED_EXIT}.get(outcome, 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("case", help="one case: Markdown table row on stdout")
    cmd.add_argument("--suite", required=True)
    cmd.add_argument("--case", required=True, help="case label, e.g. 'python 3.13, sros 25.10.R1'")
    cmd.add_argument("--outcome", default="success", help="outcome of the suite command step")
    cmd.add_argument("--setup-outcome", default="success", help="outcome of the 'make test-setup' step")
    cmd.add_argument("--junit-dir", default=DEFAULT_JUNIT_DIR)
    cmd.add_argument("--experimental", action="store_true")
    cmd.add_argument("--json", metavar="FILE", help="also write the result as JSON")
    opts = parser.parse_args(argv)

    result = read_junit(junit_files(opts.junit_dir))
    if opts.setup_outcome == "skipped":
        stage, code = "prepare", 1
    elif opts.setup_outcome != "success":
        stage, code = "setup", _outcome_exit(opts.setup_outcome)
    elif opts.outcome == "skipped":
        stage, code = "suite", 1
    else:
        stage, code = "suite", _outcome_exit(opts.outcome)
    row = evaluate(result, opts.suite, opts.case, stage, code, experimental=opts.experimental)
    sys.stdout.write(render_table([row]))
    if opts.json:
        with open(opts.json, "w", encoding="utf-8") as f:
            json.dump(row.to_dict(), f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
