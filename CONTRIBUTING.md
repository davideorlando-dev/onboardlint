# Contributing to OnboardLint

Thanks for helping improve the first-time contributor experience across open-source projects.

## Development setup

Requirements: Python 3.11 or newer and Git.

```bash
git clone https://github.com/davideorlando-dev/onboardlint.git
cd onboardlint
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

On Windows PowerShell, activate the environment with `.venv\\Scripts\\Activate.ps1`.

## Run tests

```bash
python -m pytest
```

Run lint checks with:

```bash
ruff check .
```

Tests use temporary directories. They do not require network access or execute audited repositories.

## Change guidelines

- Keep checks deterministic and explainable.
- Prefer the Python standard library for runtime functionality.
- Do not add telemetry, network access, or repository mutation.
- Give new checks stable IDs and tests for both passing and failing cases.
- Keep heuristics conservative; document false-positive and false-negative limitations.
- Update README or docs when CLI behaviour, output schema, or supported checks change.

## Pull requests

1. Open an issue first for substantial changes so the scope can be discussed.
2. Keep a pull request focused on one change.
3. Add or update tests.
4. Run `python -m pytest` and `ruff check .` locally.
5. Explain the user problem, design choice, and known limitations in the pull-request description.

By contributing, you agree that your contributions are submitted under the MIT license that covers this project.
