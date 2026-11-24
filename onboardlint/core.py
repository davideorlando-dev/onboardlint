"""Repository onboarding checks.

The audit is deliberately read-only: it inspects a bounded set of well-known
repository files and never executes project code or makes network requests.
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_MAX_TEXT_BYTES = 256_000


@dataclass(frozen=True, slots=True)
class Finding:
    """One deterministic onboarding check result."""

    check_id: str
    title: str
    category: str
    points: int
    earned: int
    status: str
    severity: str
    message: str
    recommendation: str
    path: str | None = None


@dataclass(frozen=True, slots=True)
class AuditReport:
    """Serializable result of an OnboardLint repository audit."""

    schema_version: str
    tool: str
    root: str
    score: int
    grade: str
    points_earned: int
    points_possible: int
    categories: dict[str, dict[str, int]]
    findings: tuple[Finding, ...]

    @property
    def passed(self) -> bool:
        return self.score >= 80

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation with stable field names."""
        data = asdict(self)
        data["findings"] = [asdict(item) for item in self.findings]
        data["passed"] = self.passed
        return data

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


class RepositoryReadError(ValueError):
    """Raised when a repository cannot be safely inspected."""


def _safe_path(root: Path, relative: str) -> Path | None:
    """Return a path only when no component is a symlink and it stays under root."""
    path = root / relative
    try:
        path.relative_to(root)
        current = root
        for part in Path(relative).parts:
            current = current / part
            if current.is_symlink():
                return None
        if not path.resolve(strict=False).is_relative_to(root):
            return None
        return path
    except (OSError, ValueError):
        return None


def _read_text(root: Path, relative: str) -> str:
    """Read a bounded repository text file without traversing symlinks."""
    path = _safe_path(root, relative)
    if path is None:
        return ""
    try:
        if not path.is_file() or path.stat().st_size > _MAX_TEXT_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _first_existing(root: Path, candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        path = _safe_path(root, candidate)
        try:
            if path is not None and path.is_file():
                return candidate
        except OSError:
            continue
    return None


def _contains_heading(text: str, terms: tuple[str, ...]) -> bool:
    for line in text.splitlines():
        if re.match(r"^\s{0,3}#{1,6}\s+", line):
            heading = re.sub(r"^\s{0,3}#{1,6}\s+", "", line).strip().lower()
            if any(term in heading for term in terms):
                return True
    return False


def _find_test_command(root: Path) -> tuple[str | None, str | None]:
    """Infer a common test command from project metadata without running it."""
    pyproject = _read_text(root, "pyproject.toml")
    if pyproject:
        try:
            data = tomllib.loads(pyproject)
            text = pyproject.lower()
            if "pytest" in text:
                return "python -m pytest", "pyproject.toml"
            if "unittest" in text or data.get("tool", {}).get("unittest"):
                return "python -m unittest", "pyproject.toml"
        except (tomllib.TOMLDecodeError, AttributeError):
            if "pytest" in pyproject.lower():
                return "python -m pytest", "pyproject.toml"

    package_json = _read_text(root, "package.json")
    if package_json:
        try:
            package = json.loads(package_json)
            if package.get("scripts", {}).get("test"):
                return "npm test", "package.json"
        except (json.JSONDecodeError, AttributeError):
            pass

    if _first_existing(root, ("Cargo.toml",)):
        return "cargo test", "Cargo.toml"
    if _first_existing(root, ("go.mod",)):
        return "go test ./...", "go.mod"
    if _first_existing(root, ("Makefile",)):
        makefile = _read_text(root, "Makefile")
        if re.search(r"(?m)^test\s*:", makefile):
            return "make test", "Makefile"
    return None, None


def _directory_has_tests(root: Path) -> str | None:
    for directory in ("tests", "test"):
        candidate = _safe_path(root, directory)
        try:
            if candidate is not None and candidate.is_dir():
                for index, file in enumerate(candidate.rglob("*")):
                    if index >= 5000:
                        break
                    if file.is_file() and not file.is_symlink() and file.name != "__init__.py":
                        return directory
        except OSError:
            continue
    # Common single-file test layouts.
    try:
        for file in root.iterdir():
            if file.is_file() and not file.is_symlink() and re.match(r"test_.*\.(py|js|ts|go)$", file.name):
                return file.name
    except OSError:
        pass
    return None


def _has_ci(root: Path) -> str | None:
    candidates = (
        ".github/workflows",
        ".gitlab-ci.yml",
        ".circleci/config.yml",
        "azure-pipelines.yml",
        "Jenkinsfile",
    )
    for candidate in candidates:
        path = _safe_path(root, candidate)
        try:
            if path is not None and path.is_dir():
                for file in path.glob("*"):
                    if file.is_file() and not file.is_symlink() and file.suffix.lower() in {".yml", ".yaml"}:
                        return file.relative_to(root).as_posix()
            elif path is not None and path.is_file():
                return candidate
        except OSError:
            continue
    return None


def _has_issue_template(root: Path) -> str | None:
    for directory in (".github/ISSUE_TEMPLATE", ".gitlab/issue_templates"):
        path = _safe_path(root, directory)
        try:
            if path is not None and path.is_dir():
                for file in path.iterdir():
                    if file.is_file() and not file.is_symlink() and file.suffix.lower() in {".md", ".yml", ".yaml"}:
                        return file.relative_to(root).as_posix()
        except OSError:
            continue
    return _first_existing(root, (".github/ISSUE_TEMPLATE.md",))


def _check(
    *,
    check_id: str,
    title: str,
    category: str,
    points: int,
    passed: bool,
    severity: str,
    success_message: str,
    failure_message: str,
    recommendation: str,
    path: str | None = None,
) -> Finding:
    return Finding(
        check_id=check_id,
        title=title,
        category=category,
        points=points,
        earned=points if passed else 0,
        status="pass" if passed else "fail",
        severity="none" if passed else severity,
        message=success_message if passed else failure_message,
        recommendation="No action needed." if passed else recommendation,
        path=path,
    )


def audit_repository(path: str | Path = ".") -> AuditReport:
    """Audit a local repository and return a deterministic, read-only report.

    Parameters
    ----------
    path:
        Path to the repository root. The directory must exist.

    Notes
    -----
    OnboardLint does not clone repositories, contact GitHub, execute scripts,
    install dependencies, or inspect files outside the supplied root.
    """
    requested = Path(path).expanduser()
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise RepositoryReadError(f"Cannot resolve repository path: {requested}") from exc
    if not root.is_dir():
        raise RepositoryReadError(f"Repository path is not a directory: {root}")

    readme_path = _first_existing(root, ("README.md", "README.rst", "README.txt", "README"))
    readme = _read_text(root, readme_path) if readme_path else ""
    contributing_path = _first_existing(root, ("CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING"))
    contributing = _read_text(root, contributing_path) if contributing_path else ""
    license_path = _first_existing(root, ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"))
    conduct_path = _first_existing(root, ("CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.rst"))
    security_path = _first_existing(root, ("SECURITY.md", "SECURITY.rst"))
    pr_template_path = _first_existing(
        root,
        (
            ".github/pull_request_template.md",
            ".github/PULL_REQUEST_TEMPLATE.md",
            "PULL_REQUEST_TEMPLATE.md",
            ".gitlab/merge_request_templates/Default.md",
        ),
    )
    issue_template_path = _has_issue_template(root)
    ci_path = _has_ci(root)
    tests_path = _directory_has_tests(root)
    test_command, test_manifest = _find_test_command(root)
    manifest_path = _first_existing(
        root,
        (
            "pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml",
            "build.gradle", "Gemfile", "composer.json", "Package.swift",
        ),
    )

    findings = [
        _check(
            check_id="DOC-001", title="Project overview exists", category="Documentation", points=10,
            passed=bool(readme_path), severity="high",
            success_message=f"Found project overview at {readme_path}.",
            failure_message="No README or equivalent project overview was found.",
            recommendation="Add a README that explains what the project does, who it serves, and how to get started.",
            path=readme_path,
        ),
        _check(
            check_id="DOC-002", title="README explains installation or quickstart", category="Documentation", points=5,
            passed=bool(readme and _contains_heading(readme, ("install", "quickstart", "quick start", "getting started", "setup"))),
            severity="medium", success_message="README has an installation or quickstart section.",
            failure_message="README does not have a recognisable installation or quickstart section.",
            recommendation="Add a short, copy-pasteable first-run path with prerequisites and expected output.",
            path=readme_path,
        ),
        _check(
            check_id="DOC-003", title="README includes usage guidance", category="Documentation", points=5,
            passed=bool(readme and _contains_heading(readme, ("usage", "examples", "example", "how to use"))),
            severity="low", success_message="README has a usage or examples section.",
            failure_message="README does not have a recognisable usage or examples section.",
            recommendation="Add one minimal working example showing the main user workflow.",
            path=readme_path,
        ),
        _check(
            check_id="GOV-001", title="Open-source license is present", category="Governance", points=10,
            passed=bool(license_path), severity="high",
            success_message=f"Found license file at {license_path}.",
            failure_message="No standard license file was found.",
            recommendation="Choose an OSI-approved license that matches the project's goals and add its full text.",
            path=license_path,
        ),
        _check(
            check_id="CON-001", title="Contribution guide exists", category="Contribution path", points=10,
            passed=bool(contributing_path), severity="high",
            success_message=f"Found contribution guide at {contributing_path}.",
            failure_message="No CONTRIBUTING guide was found.",
            recommendation="Add CONTRIBUTING.md with local setup, development workflow, tests, style, and pull-request expectations.",
            path=contributing_path,
        ),
        _check(
            check_id="CON-002", title="Contribution guide explains how to run tests", category="Contribution path", points=5,
            passed=bool(contributing and re.search(r"\b(test|testing|pytest|unittest|cargo test|npm test|go test)\b", contributing, re.I)),
            severity="medium", success_message="Contribution guide mentions testing or a test command.",
            failure_message="Contribution guide does not explain how contributors can run tests.",
            recommendation="Document the exact test command, required services, and any environment variables.",
            path=contributing_path,
        ),
        _check(
            check_id="GOV-002", title="Code of Conduct exists", category="Governance", points=5,
            passed=bool(conduct_path), severity="low",
            success_message=f"Found community conduct policy at {conduct_path}.",
            failure_message="No Code of Conduct was found.",
            recommendation="Add a clear, enforceable community Code of Conduct and identify a reporting route.",
            path=conduct_path,
        ),
        _check(
            check_id="GOV-003", title="Security reporting policy exists", category="Governance", points=5,
            passed=bool(security_path), severity="medium",
            success_message=f"Found security policy at {security_path}.",
            failure_message="No security disclosure instructions were found.",
            recommendation="Add SECURITY.md describing supported versions and a private vulnerability-reporting channel.",
            path=security_path,
        ),
        _check(
            check_id="CON-003", title="Pull-request template exists", category="Contribution path", points=5,
            passed=bool(pr_template_path), severity="low",
            success_message=f"Found pull-request template at {pr_template_path}.",
            failure_message="No pull-request template was found.",
            recommendation="Add a template asking for context, linked issues, test evidence, and compatibility impact.",
            path=pr_template_path,
        ),
        _check(
            check_id="CON-004", title="Issue template exists", category="Contribution path", points=5,
            passed=bool(issue_template_path), severity="low",
            success_message=f"Found issue template at {issue_template_path}.",
            failure_message="No issue template was found.",
            recommendation="Add bug-report and feature-request templates that collect reproducible information.",
            path=issue_template_path,
        ),
        _check(
            check_id="AUTO-001", title="Continuous-integration workflow exists", category="Automation", points=10,
            passed=bool(ci_path), severity="medium",
            success_message=f"Found automation configuration at {ci_path}.",
            failure_message="No common CI configuration was found.",
            recommendation="Add CI that runs formatting, static checks, and tests on supported runtimes.",
            path=ci_path,
        ),
        _check(
            check_id="TEST-001", title="Test suite is present", category="Automation", points=10,
            passed=bool(tests_path), severity="high",
            success_message=f"Found a test directory or test file at {tests_path}.",
            failure_message="No recognisable test directory or test file was found.",
            recommendation="Add automated tests for core behaviour and failure cases; run them in CI.",
            path=tests_path,
        ),
        _check(
            check_id="META-001", title="Project manifest exists", category="Project metadata", points=5,
            passed=bool(manifest_path), severity="low",
            success_message=f"Found a project manifest at {manifest_path}.",
            failure_message="No common project manifest was found.",
            recommendation="Add the relevant package or build manifest so contributors can identify tooling and dependencies.",
            path=manifest_path,
        ),
        _check(
            check_id="DOC-004", title="Dedicated documentation directory exists", category="Documentation", points=5,
            passed=(_safe_path(root, "docs") is not None and (root / "docs").is_dir()), severity="low",
            success_message="Found a docs/ directory.",
            failure_message="No docs/ directory was found.",
            recommendation="Add a docs/ directory for architecture, configuration, troubleshooting, and deeper guides.",
            path="docs" if (_safe_path(root, "docs") is not None and (root / "docs").is_dir()) else None,
        ),
    ]

    # A stronger, project-aware check: do the contributor instructions mention
    # the test command inferred from metadata, rather than just the word 'tests'?
    if test_command:
        has_documented_command = test_command.lower() in contributing.lower()
        findings.append(_check(
            check_id="CON-005", title="Documented test command matches project metadata",
            category="Contribution path", points=5, passed=has_documented_command,
            severity="medium",
            success_message=f"Contribution guide documents `{test_command}` (inferred from {test_manifest}).",
            failure_message=f"Project metadata suggests `{test_command}`, but CONTRIBUTING does not document it.",
            recommendation=f"Add the exact command `{test_command}` to CONTRIBUTING.md and keep it aligned with CI.",
            path=contributing_path,
        ))
    else:
        findings.append(_check(
            check_id="CON-005", title="A standard test command can be inferred",
            category="Contribution path", points=5, passed=False, severity="low",
            success_message="Inferred a standard test command from project metadata.",
            failure_message="Could not infer a standard test command from common project manifests.",
            recommendation="Document a single canonical test command and configure it in the project manifest or Makefile.",
            path=manifest_path,
        ))

    points_possible = sum(item.points for item in findings)
    points_earned = sum(item.earned for item in findings)
    score = round((points_earned / points_possible) * 100) if points_possible else 0
    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 65 else "D" if score >= 50 else "F"
    categories: dict[str, dict[str, int]] = {}
    for item in findings:
        bucket = categories.setdefault(item.category, {"earned": 0, "possible": 0})
        bucket["earned"] += item.earned
        bucket["possible"] += item.points

    return AuditReport(
        schema_version="1.0",
        tool="onboardlint",
        root=str(root),
        score=score,
        grade=grade,
        points_earned=points_earned,
        points_possible=points_possible,
        categories=categories,
        findings=tuple(findings),
    )
