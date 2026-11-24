# Design principles

1. **Read-only by default.** An audit must never modify a repository.
2. **No execution.** Do not run tests, package hooks, build scripts, or arbitrary project code.
3. **Explain every point.** Every score component has a stable check ID and an actionable explanation.
4. **No popularity proxies.** Stars, downloads, and commit counts do not measure newcomer experience.
5. **Heuristics are not truth.** The tool should disclose what it cannot assess and invite maintainers to inspect findings.
6. **Small runtime footprint.** Prefer the standard library and local execution.
7. **Inclusive defaults.** Support different contribution models; do not require a single governance structure or hosting provider.
