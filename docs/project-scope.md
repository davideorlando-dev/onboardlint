# Project scope and limitations

OnboardLint audits local repository signals that affect a new contributor's ability to discover the project, understand the development workflow, and find the expected quality gates.

It is intentionally not a full repository-health platform. It does not estimate bus factor, dependency criticality, vulnerability exposure, community sentiment, maintainer response time, or project adoption. Those metrics require different evidence and can be misleading without context.

The current checks are structural heuristics. A present `SECURITY.md` may be incomplete; a test directory may contain weak tests; a CI workflow may not actually pass. Future versions should add opt-in deeper checks only when they can remain safe, deterministic, and understandable.
