#!/usr/bin/env python3
# version: 1
# Copied from nokia-steward-validator pattern/. Do not edit: the linter checks this file is unchanged.
"""
Read .github/test-matrix.yml: validate it, expand its cases and route them by capability.

GitHub Actions (.github/workflows/ci.yml) and nokia-steward-validator both use this file, so a case
means the same thing wherever it runs.

  matrix.py validate [FILE]                        check the file, print errors
  matrix.py list [FILE] [--provides CAPS]          one line per case, with what it needs
  matrix.py github [FILE] --provides CAPS          GITHUB_OUTPUT lines for ci.yml (cases, count)
  matrix.py env [FILE] --case ID                   NAME=value lines a case exports

Needs PyYAML.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field

import yaml

VERSION = 1
DEFAULT_FILE = ".github/test-matrix.yml"
DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 360

TOOLCHAINS = ("python", "go", "rust", "node")
SERVICES = ("docker", "containerlab", "kubernetes", "helm")
CAPABILITIES = (*SERVICES, "srlinux", "srsim")
# What a GitHub-hosted runner provides; srsim is added when the SRSIM_LICENSE secret exists.
GITHUB_PROVIDES = ("docker", "containerlab", "kubernetes", "helm", "srlinux")
# Capabilities that need containerlab on the host.
LAB_CAPABILITIES = ("srlinux", "srsim")

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SUITE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
VALUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+/-]*$")
APT_RE = re.compile(r"^[a-z0-9][a-z0-9.+-]*$")
RESERVED_ENV = ("PATH", "HOME", "STEWARD_SUITE", "STEWARD_CASE")

TOP_KEYS = ("version", "environment", "inputs", "suites")
ENVIRONMENT_KEYS = ("services", "apt")
INPUT_KEYS = ("toolchain", "env", "requires")
SUITE_KEYS = ("run", "timeout_minutes", "requires", "cases")


class ManifestError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class Case:
    suite: str
    run: str
    timeout_minutes: int
    values: dict[str, str]
    experimental: bool
    requires: tuple[str, ...]
    toolchains: dict[str, str] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)

    @property
    def label(self) -> str:
        """What varies in this case, e.g. 'python 3.13, ansible 2.22, sros 25.10.R1'."""
        return ", ".join(f"{k} {v}" for k, v in self.values.items()) or "default"

    @property
    def id(self) -> str:
        """Unique, file-name safe, e.g. 'integration-sros-python3.13-ansible2.22-sros25.10.R1'."""
        parts = [self.suite, *(f"{k}{v}" for k, v in self.values.items())]
        return re.sub(r"[^A-Za-z0-9._-]", "-", "-".join(parts))

    @property
    def name(self) -> str:
        suffix = ", experimental" if self.experimental else ""
        return f"{self.suite} ({self.label}{suffix})"

    def missing(self, provides: set[str] | tuple[str, ...]) -> list[str]:
        return [cap for cap in self.requires if cap not in provides]


##############################################################################
# Validation
##############################################################################


def _string_list(value, where: str, errors: list[str]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        errors.append(f"{where}: must be a list of strings")
        return []
    return value


def _check_keys(node: dict, allowed: tuple[str, ...], where: str, errors: list[str]) -> None:
    for key in node:
        if key not in allowed:
            errors.append(f"{where}: unknown key '{key}' (allowed: {', '.join(allowed)})")


def _capabilities(value, where: str, errors: list[str]) -> list[str]:
    caps = _string_list(value, where, errors)
    for cap in caps:
        if cap not in CAPABILITIES:
            errors.append(f"{where}: unknown capability '{cap}' (known: {', '.join(CAPABILITIES)})")
    return caps


def validate(data) -> list[str]:
    """All problems of a parsed test-matrix.yml; empty when it is valid."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["the file must be a YAML mapping"]
    _check_keys(data, TOP_KEYS, "top level", errors)

    version = data.get("version")
    if version != VERSION:
        errors.append(f"version: must be {VERSION} (found {version!r})")

    environment = data.get("environment") or {}
    if not isinstance(environment, dict):
        errors.append("environment: must be a mapping")
        environment = {}
    _check_keys(environment, ENVIRONMENT_KEYS, "environment", errors)
    for service in _string_list(environment.get("services"), "environment.services", errors):
        if service not in SERVICES:
            errors.append(f"environment.services: unknown service '{service}' (known: {', '.join(SERVICES)})")
    for package in _string_list(environment.get("apt"), "environment.apt", errors):
        if not APT_RE.match(package):
            errors.append(f"environment.apt: invalid package name '{package}'")

    inputs = data.get("inputs") or {}
    if not isinstance(inputs, dict):
        errors.append("inputs: must be a mapping")
        inputs = {}
    seen_toolchains: dict[str, str] = {}
    seen_env: dict[str, str] = {}
    for key, spec in inputs.items():
        where = f"inputs.{key}"
        if not isinstance(key, str) or not NAME_RE.match(key) or key == "experimental":
            errors.append(f"{where}: name must be lower case letters, digits and '_' (and not 'experimental')")
        if not isinstance(spec, dict):
            errors.append(f"{where}: must be a mapping with toolchain, env and/or requires")
            continue
        _check_keys(spec, INPUT_KEYS, where, errors)
        if "toolchain" not in spec and "env" not in spec:
            errors.append(f"{where}: needs 'toolchain' or 'env' (or both)")
        toolchain = spec.get("toolchain")
        if toolchain is not None:
            if toolchain not in TOOLCHAINS:
                errors.append(f"{where}.toolchain: must be one of {', '.join(TOOLCHAINS)}")
            elif toolchain in seen_toolchains:
                errors.append(f"{where}.toolchain: {toolchain} is already set by inputs.{seen_toolchains[toolchain]}")
            else:
                seen_toolchains[toolchain] = key
        env = spec.get("env")
        if env is not None:
            if not isinstance(env, str) or not ENV_RE.match(env) or env in RESERVED_ENV:
                errors.append(f"{where}.env: must be an upper case variable name, not {', '.join(RESERVED_ENV)}")
            elif env in seen_env:
                errors.append(f"{where}.env: {env} is already set by inputs.{seen_env[env]}")
            else:
                seen_env[env] = key
        _capabilities(spec.get("requires"), f"{where}.requires", errors)

    suites = data.get("suites")
    if not isinstance(suites, dict) or not suites:
        errors.append("suites: must be a mapping with at least one suite")
        return errors
    for suite, spec in suites.items():
        where = f"suites.{suite}"
        if not isinstance(suite, str) or not SUITE_RE.match(suite):
            errors.append(f"{where}: name must be lower case letters, digits and '-'")
        if not isinstance(spec, dict):
            errors.append(f"{where}: must be a mapping with run and cases")
            continue
        _check_keys(spec, SUITE_KEYS, where, errors)
        run = spec.get("run")
        if not isinstance(run, str) or not run.strip() or "\n" in run.strip():
            errors.append(f"{where}.run: must be one command line, e.g. 'make test-{suite}'")
        timeout = spec.get("timeout_minutes", DEFAULT_TIMEOUT)
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= MAX_TIMEOUT:
            errors.append(f"{where}.timeout_minutes: must be a whole number of minutes, 1 to {MAX_TIMEOUT}")
        _capabilities(spec.get("requires"), f"{where}.requires", errors)
        cases = spec.get("cases")
        if not isinstance(cases, list) or not cases:
            errors.append(f"{where}.cases: must be a list with at least one case")
            continue
        seen_cases = []
        for index, case in enumerate(cases):
            cwhere = f"{where}.cases[{index}]"
            if case is None:
                case = {}
            if not isinstance(case, dict):
                errors.append(f"{cwhere}: must be a mapping of input to value, e.g. {{python: '3.13'}}")
                continue
            for key, value in case.items():
                if key == "experimental":
                    if not isinstance(value, bool):
                        errors.append(f"{cwhere}.experimental: must be true or false")
                    continue
                if key not in inputs:
                    errors.append(f"{cwhere}: '{key}' is not declared under inputs")
                if isinstance(value, float):
                    errors.append(f"{cwhere}.{key}: quote versions: YAML read this as the number {value}")
                elif isinstance(value, bool) or not isinstance(value, (str, int)) or not VALUE_RE.match(str(value)):
                    errors.append(f"{cwhere}.{key}: use letters, digits, '.', '_', '+', '/' or '-'")
            values = {k: v for k, v in case.items() if k != "experimental"}
            if values in seen_cases:
                errors.append(f"{cwhere}: duplicate case")
            seen_cases.append(values)
    return errors


def load(path: str = DEFAULT_FILE) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except OSError as e:
        raise ManifestError([f"cannot read {path}: {e}"]) from e
    except yaml.YAMLError as e:
        raise ManifestError([f"{path} is not valid YAML: {e}"]) from e
    errors = validate(data)
    if errors:
        raise ManifestError([f"{path}: {e}" for e in errors])
    return data


##############################################################################
# Expansion and routing
##############################################################################


def expand(data: dict) -> list[Case]:
    """Every case of every suite, in file order. The data must be valid."""
    services = list((data.get("environment") or {}).get("services") or [])
    inputs = data.get("inputs") or {}
    cases = []
    for suite, spec in data["suites"].items():
        for raw in spec["cases"]:
            raw = raw or {}
            values = {k: str(v) for k, v in raw.items() if k != "experimental"}
            requires = set(services) | set(spec.get("requires") or [])
            toolchains, env = {}, {}
            for key, value in values.items():
                spec_in = inputs[key]
                requires |= set(spec_in.get("requires") or [])
                if spec_in.get("toolchain"):
                    toolchains[spec_in["toolchain"]] = value
                if spec_in.get("env"):
                    env[spec_in["env"]] = value
            if requires & set(LAB_CAPABILITIES):
                requires |= {"docker", "containerlab"}
            if "kubernetes" in requires:
                requires.add("docker")
            cases.append(
                Case(
                    suite=suite,
                    run=spec["run"].strip(),
                    timeout_minutes=spec.get("timeout_minutes", DEFAULT_TIMEOUT),
                    values=values,
                    experimental=bool(raw.get("experimental", False)),
                    requires=tuple(c for c in CAPABILITIES if c in requires),
                    toolchains=toolchains,
                    env=env,
                )
            )
    return cases


def case_env(case: Case) -> dict[str, str]:
    """Variables a case exports before 'make test-setup' and the suite command."""
    return {**case.env, "STEWARD_SUITE": case.suite, "STEWARD_CASE": case.id}


def route(cases: list[Case], provides) -> tuple[list[Case], list[Case]]:
    """(cases this executor can run, cases it cannot)."""
    provided = set(provides)
    runnable = [c for c in cases if not c.missing(provided)]
    unmet = [c for c in cases if c.missing(provided)]
    return runnable, unmet


def parse_provides(text: str) -> set[str]:
    caps = {c.strip() for c in text.split(",") if c.strip()}
    unknown = caps - set(CAPABILITIES)
    if unknown:
        raise ManifestError([f"unknown capability {', '.join(sorted(unknown))} in --provides"])
    return caps


def github_entry(case: Case, apt: list[str]) -> dict:
    """One strategy.matrix include entry for ci.yml."""
    entry = {
        "name": case.name,
        "id": case.id,
        "suite": case.suite,
        "label": case.label,
        "run": case.run,
        "timeout": case.timeout_minutes,
        "experimental": case.experimental,
        "env": case_env(case),
        "apt": " ".join(apt),
    }
    for tool in TOOLCHAINS:
        entry[tool] = case.toolchains.get(tool, "")
    for cap in ("containerlab", "kubernetes", "helm", "srsim"):
        entry[cap] = cap in case.requires
    return entry


def skipped_markdown(unmet: list[Case], provides: set[str]) -> str:
    if not unmet:
        return ""
    lines = [
        "### Cases not run on GitHub",
        "",
        "These cases need a capability this runner does not provide. nokia-steward-validator runs them.",
        "",
        "| Suite | Case | Needs |",
        "| --- | --- | --- |",
    ]
    for case in unmet:
        lines.append(f"| {case.suite} | {case.label} | {', '.join(case.missing(provides))} |")
    return "\n".join(lines) + "\n"


##############################################################################
# CLI
##############################################################################


def _find(cases: list[Case], case_id: str) -> Case:
    for case in cases:
        if case.id == case_id:
            return case
    raise ManifestError([f"no case '{case_id}'; run 'matrix.py list' to see the ids"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "list", "github", "env"):
        cmd = sub.add_parser(name)
        cmd.add_argument("file", nargs="?", default=DEFAULT_FILE)
        if name in ("list", "github"):
            cmd.add_argument("--provides", default=",".join(CAPABILITIES), help="comma separated capabilities")
        if name == "env":
            cmd.add_argument("--case", required=True, help="case id, see 'list'")
    opts = parser.parse_args(argv)

    try:
        data = load(opts.file)
        cases = expand(data)
        if opts.command == "validate":
            print(f"{opts.file}: OK, {len(cases)} case(s) in {len(data['suites'])} suite(s)")
        elif opts.command == "list":
            provides = parse_provides(opts.provides)
            for case in cases:
                missing = case.missing(provides)
                where = f"needs {', '.join(missing)}" if missing else "runnable"
                print(f"{case.id}  [{where}]  requires: {', '.join(case.requires) or '-'}")
        elif opts.command == "github":
            provides = parse_provides(opts.provides)
            runnable, unmet = route(cases, provides)
            apt = list((data.get("environment") or {}).get("apt") or [])
            include = [github_entry(c, apt) for c in runnable]
            print(f"cases={json.dumps(include, separators=(',', ':'))}")
            print(f"count={len(include)}")
            summary = os.environ.get("GITHUB_STEP_SUMMARY")
            text = skipped_markdown(unmet, provides)
            if summary and text:
                with open(summary, "a", encoding="utf-8") as f:
                    f.write(text)
            for case in unmet:
                print(
                    f"skipped on this runner: {case.name}, needs {', '.join(case.missing(provides))}", file=sys.stderr
                )
        elif opts.command == "env":
            for key, value in case_env(_find(cases, opts.case)).items():
                print(f"{key}={value}")
    except ManifestError as e:
        for error in e.errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
