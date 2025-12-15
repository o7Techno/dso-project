# P10 SAST & Secrets summary

- Workflow: `Security - SAST & Secrets` (Semgrep + Gitleaks) — runs on push/PR for code + security configs and manual dispatch.
- Artifacts: `EVIDENCE/P10/semgrep.sarif`, `EVIDENCE/P10/gitleaks.json` (uploaded as artifact `P10_EVIDENCE`; keep latest run for traceability).
- Semgrep config: profile `p/ci` + custom rules in `security/semgrep/rules.yml` (HTMLResponse f-strings, httpx verify=False).
- Gitleaks config: `security/.gitleaks.toml` with allowlist for evidence artifacts and UUID-shaped correlation IDs in docs/tests (documented false positive).

## Latest triage (update after each run)
- Semgrep findings: 0 (p/ci + custom rules). Action: no code changes needed; keep monitoring in CI.
- Gitleaks findings: 0 real secrets. False positives: correlation UUIDs in docs/tests allowed via regex allowlist; no real secrets detected.
- Critical secret policy: any cloud/API keys, database URLs, JWT signing keys, or credentials in code/config must be rotated and removed; add scoped secrets to GitHub/CI only. False positives should be allowlisted with path/regex + comment.

## Backlog / follow-ups
- Integrate findings into DS/PR: link to successful workflow run, reference artifacts above.
- If future findings appear: fix high/medium immediately or create issue linking to `semgrep.sarif`/`gitleaks.json` with owner and due date.
