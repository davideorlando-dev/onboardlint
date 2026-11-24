# JSON report schema (v1)

The JSON report is versioned by `schema_version`. Consumers should ignore unknown fields so new optional metadata can be added without breaking readers.

Top-level fields:

- `schema_version`: report contract version (`1.0`).
- `tool`: tool identifier (`onboardlint`).
- `root`: absolute local path that was audited.
- `score`, `grade`: transparent weighted checklist score.
- `points_earned`, `points_possible`: score numerator and denominator.
- `categories`: per-category points.
- `findings`: ordered check results, each with stable `check_id`, status, severity, points, message, recommendation, and optional path.
- `passed`: true when the score is at least 80. This is a convenience field, not a security or quality certification.

Example:

```json
{
  "schema_version": "1.0",
  "tool": "onboardlint",
  "score": 80,
  "grade": "B",
  "passed": true,
  "findings": []
}
```

The example is abbreviated. A real report includes all documented top-level fields and every check result.
