# Scoring model

OnboardLint uses a fixed weighted checklist. Each check is worth a defined number of points; passing earns all points and failing earns zero. The score is the rounded percentage of earned points over all possible points.

| Category | Maximum points |
|---|---:|
| Documentation | 25 |
| Governance | 20 |
| Contribution path | 30 |
| Automation | 20 |
| Project metadata | 5 |
| **Total** | **100** |

Grades are descriptive bands: A (90–100), B (80–89), C (65–79), D (50–64), F (0–49). The CLI's `--min-score` option is an independent CI threshold and defaults to 0.

A passing score is not a certification. The tool tests for observable repository signals, not the quality of every policy or whether the project is genuinely welcoming. Maintainers should review findings and adapt the checks to their project's governance model.
