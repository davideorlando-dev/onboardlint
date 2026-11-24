from __future__ import annotations

import json
from pathlib import Path

import pytest

from onboardlint import RepositoryReadError, audit_repository


def _write(root: Path, relative: str, content: str = "content\\n") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_empty_repository_returns_actionable_findings(tmp_path: Path) -> None:
    report = audit_repository(tmp_path)
    assert report.score == 0
    assert report.grade == "F"
    assert len(report.findings) >= 10
    assert any(item.check_id == "DOC-001" and item.status == "fail" for item in report.findings)


def test_detects_documentation_and_matching_test_command(tmp_path: Path) -> None:
    _write(tmp_path, "README.md", "# Demo\\n## Installation\\nInstall it.\\n## Usage\\nRun it.\\n")
    _write(tmp_path, "LICENSE", "MIT License\\n")
    _write(tmp_path, "CONTRIBUTING.md", "# Contributing\\n## Setup\\n## Tests\\nRun `python -m pytest`.\\n")
    _write(tmp_path, "CODE_OF_CONDUCT.md")
    _write(tmp_path, "SECURITY.md")
    _write(tmp_path, ".github/pull_request_template.md")
    _write(tmp_path, ".github/ISSUE_TEMPLATE/bug.yml")
    _write(tmp_path, ".github/workflows/ci.yml", "name: CI\\n")
    _write(tmp_path, "tests/test_demo.py", "def test_demo(): pass\\n")
    _write(tmp_path, "docs/index.md")
    _write(tmp_path, "pyproject.toml", "[project]\\nname='demo'\\n[project.optional-dependencies]\\ntest=['pytest']\\n")

    report = audit_repository(tmp_path)
    checks = {item.check_id: item for item in report.findings}
    assert checks["CON-005"].status == "pass"
    assert checks["AUTO-001"].status == "pass"
    assert report.score == 100
    assert report.grade == "A"


def test_flags_mismatch_between_manifest_and_contributing(tmp_path: Path) -> None:
    _write(tmp_path, "pyproject.toml", "[project]\\nname='demo'\\n[tool.pytest.ini_options]\\ntestpaths=['tests']\\n")
    _write(tmp_path, "CONTRIBUTING.md", "# Contributing\\n## Tests\\nRun tests locally.\\n")
    report = audit_repository(tmp_path)
    check = next(item for item in report.findings if item.check_id == "CON-005")
    assert check.status == "fail"
    assert "python -m pytest" in check.message


def test_json_output_is_machine_readable(tmp_path: Path) -> None:
    report = audit_repository(tmp_path)
    parsed = json.loads(report.to_json())
    assert parsed["schema_version"] == "1.0"
    assert parsed["tool"] == "onboardlint"
    assert isinstance(parsed["findings"], list)
    assert parsed["passed"] is False


def test_rejects_non_directory_path(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(RepositoryReadError):
        audit_repository(file_path)


def test_does_not_follow_symlinked_repository_directories(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "README.md").write_text("# Hidden README\\n## Installation\\n", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    try:
        (repo / "docs").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks are not available on this platform")

    report = audit_repository(repo)
    doc_check = next(item for item in report.findings if item.check_id == "DOC-004")
    assert doc_check.status == "fail"
