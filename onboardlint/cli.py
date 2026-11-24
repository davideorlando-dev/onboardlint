"""Command-line interface for OnboardLint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import RepositoryReadError, audit_repository


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="onboardlint",
        description="Audit whether a repository is ready for first-time contributors.",
    )
    parser.add_argument("path", nargs="?", default=".", help="repository directory (default: current directory)")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="output format")
    parser.add_argument("--output", type=Path, help="write the report to this file")
    parser.add_argument("--min-score", type=int, default=0, help="exit with status 1 if score is below this value (0-100)")
    parser.add_argument("--quiet", action="store_true", help="suppress text summary; JSON output is not suppressed")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not 0 <= args.min_score <= 100:
        parser.error("--min-score must be between 0 and 100")

    try:
        report = audit_repository(args.path)
    except RepositoryReadError as exc:
        print(f"onboardlint: error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        output = report.to_json() + "\n"
    else:
        lines = [
            f"OnboardLint · {Path(report.root).name}",
            f"Score: {report.score}/100  Grade: {report.grade}",
            "",
        ]
        for category, values in report.categories.items():
            possible = values["possible"]
            earned = values["earned"]
            lines.append(f"{category}: {earned}/{possible}")
        lines.append("")
        for finding in report.findings:
            marker = "✓" if finding.status == "pass" else "!"
            location = f" ({finding.path})" if finding.path else ""
            lines.append(f"{marker} [{finding.check_id}] {finding.title}{location}")
            if finding.status == "fail":
                lines.append(f"  {finding.message}")
                lines.append(f"  Fix: {finding.recommendation}")
        lines.append("")
        lines.append("Read-only audit: OnboardLint does not execute project code or access the network.")
        output = "\n".join(lines) + "\n"

    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        except OSError as exc:
            print(f"onboardlint: cannot write report: {exc}", file=sys.stderr)
            return 2
        if not args.quiet:
            print(f"Report written to {args.output}")
    elif not args.quiet or args.format == "json":
        sys.stdout.write(output)

    return 1 if report.score < args.min_score else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
