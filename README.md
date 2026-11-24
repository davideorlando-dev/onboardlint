# OnboardLint

**A quality gate for the first-time contributor experience.**

OnboardLint checks whether a software repository gives a new contributor a clear path from “I found this project” to “I can run the tests and open a useful pull request.” It audits onboarding documentation, contribution instructions, governance files, templates, test setup, and continuous integration.

The goal is deliberately narrow: make contributor friction visible, explainable, and fixable before it quietly drives people away.

> **Status:** early alpha (0.1.0). The checks are heuristic and should be treated as actionable signals—not as a certification of project quality, security, or governance.

## Why this exists

Open-source projects often have code that works for maintainers but an incomplete path for everyone else. A README may explain what a project does without showing how to install it. A CONTRIBUTING guide may say “run the tests” without naming the actual command. A CI workflow may enforce requirements that contributors cannot discover until their pull request fails.

OnboardLint makes these gaps visible with a deterministic, local audit. It does not attempt to rank project popularity or judge code quality.

## What it checks

| Area | Checks |
|---|---|
| Documentation | README, installation/quickstart guidance, usage examples, dedicated docs directory |
| Contribution path | CONTRIBUTING guide, test instructions, pull-request template, issue template |
| Governance | License, Code of Conduct, security disclosure policy |
| Automation | CI configuration and a recognisable test suite |
| Project metadata | Common package/build manifest |
| Documentation drift | Whether the contribution guide documents the test command inferred from common project metadata |

Each check has a stable ID, a weight, a result, and a concrete recommendation. The score is a transparent checklist score, not a machine-learning prediction.

## Installation

Python 3.11 or newer is required. The runtime has no third-party dependencies.

Until the first PyPI release, install directly from the public GitHub repository:

```bash
python -m pip install git+https://github.com/davideorlando-dev/onboardlint.git
```

For local development, clone the source and install the development extras:

```bash
git clone https://github.com/davideorlando-dev/onboardlint.git
cd onboardlint
python -m pip install -e '.[dev]'
```

## Quickstart

Run an audit from the root of a repository:

```bash
onboardlint .
```

## Usage

Audit the current repository:

```bash
onboardlint .
```

Audit another local repository and require a score of at least 80:

```bash
onboardlint ../my-project --min-score 80
```

Export a machine-readable report for CI or later analysis:

```bash
onboardlint . --format json --output onboardlint-report.json
```

Example output:

```text
OnboardLint · my-project
Score: 75/100  Grade: C

Documentation: 20/25
Governance: 15/20
Contribution path: 20/30
Automation: 15/20
Project metadata: 5/5

✓ [DOC-001] Project overview exists (README.md)
! [CON-005] Documented test command matches project metadata (CONTRIBUTING.md)
  Project metadata suggests `python -m pytest`, but CONTRIBUTING does not document it.
  Fix: Add the exact command `python -m pytest` to CONTRIBUTING.md and keep it aligned with CI.
```

The output above is illustrative; actual results depend on the repository being audited.

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Audit completed and the score met `--min-score` (or no threshold was set) |
| `1` | Audit completed, but the score was below `--min-score` |
| `2` | Invalid repository path or report could not be written |

## Safety and privacy

- **Local-first:** no network requests, analytics, telemetry, or account are used.
- **Read-only:** repository files are never changed.
- **No code execution:** scripts, tests, package hooks, and build commands are never run.
- **Bounded reads:** inspected text files are capped at 256 KB.
- **No popularity scoring:** stars, downloads, contributors, and commit counts are not part of the score.

OnboardLint is not a security scanner, license opinion, governance certification, or substitute for maintainer judgment. A file can exist and still be inadequate; the current version checks structure and selected content signals, not whether every policy is substantively correct.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
ruff check .
```

The test suite uses temporary repositories and does not access the network.

## Contributing

Contributions are welcome. Start with an issue describing the repository type and the contributor problem you observed. For a pull request, include a test that reproduces the behaviour and update the documentation if a check or output field changes.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Roadmap

See [ROADMAP.md](ROADMAP.md) for proposed work. Priorities will be shaped by maintainer and contributor feedback; no roadmap item is a promise or release commitment.

## License

MIT. See [LICENSE](LICENSE).
