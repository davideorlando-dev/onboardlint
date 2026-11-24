from __future__ import annotations

import json
from pathlib import Path

from onboardlint.cli import main


def test_cli_json_and_min_score(tmp_path: Path, capsys) -> None:
    result = main([str(tmp_path), "--format", "json", "--min-score", "80"])
    captured = capsys.readouterr()
    assert result == 1
    assert json.loads(captured.out)["score"] == 0


def test_cli_writes_report_file(tmp_path: Path, capsys) -> None:
    destination = tmp_path / "reports" / "audit.json"
    result = main([str(tmp_path), "--format", "json", "--output", str(destination), "--quiet"])
    assert result == 0
    assert destination.exists()
    assert json.loads(destination.read_text(encoding="utf-8"))["tool"] == "onboardlint"
    assert capsys.readouterr().out == ""
