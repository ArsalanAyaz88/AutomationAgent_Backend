<!--
Sync Impact Report
- Version change: (init) → 1.0.0
- Modified principles: N/A (initial definition)
- Added sections: Core Principles, Additional Constraints, Development Workflow, Governance
- Removed sections: Template placeholders
- Templates requiring updates:
  ✅ .specify/templates/plan-template.md
  ✅ .specify/templates/spec-template.md
  ✅ .specify/templates/tasks-template.md
- Follow-up TODOs:
  - TODO(RATIFICATION_DATE): Provide original adoption date
-->

# YouTube Automation AI Agents Constitution

## Core Principles

### I. Data-Driven Content Strategy
All key decisions MUST be grounded in agent outputs and measurable signals.
- Agent 1 channel audits and Agent 2 title/thumbnail/keyword/hook audits are the single
  source of truth for downstream steps.
- Inputs/outputs MUST be persisted with IDs for traceability and later reuse.
- Derived guidance (patterns, formulas, hooks) MUST reference the originating data.

### II. API-First, Contract-Driven
Each agent exposes a stable FastAPI endpoint with explicit Pydantic schemas.
- Request/response contracts MUST be versioned; breaking changes require a MINOR/MAJOR bump.
- Swagger `/docs` MUST remain valid; CI checks MUST fail on schema drift.
- Frontend integrates only through these contracts.

### III. Testable, Measurable Outcomes
Every agent MUST define success criteria and validation steps.
- Agent 2: Detect title/thumbnail patterns, hooks, text/texture placement, keyword usage.
- Agent 3: Scripts MUST map back to Agent 2 insights with explicit citations.
- Agent 4: Scene boundaries and camera/angle prompts MUST be deterministically produced.
- Agent 5/6: Title/thumbnail variants and roadmaps MUST list rationale from upstream data.

### IV. Reproducibility & Saved Responses
Any result MUST be re-creatable with the same inputs.
- Use MongoDB saved-responses for versioned artifacts (content + timestamps).
- Include minimal golden datasets per agent for deterministic tests.

### V. Responsible AI & Compliance
Comply with platform ToS and provider policies.
- Respect API quotas and rate limits; implement retries with backoff.
- Clearly label generated vs sourced data; secure all keys in `.env`.
- No scraping beyond official APIs; attribute sources where applicable.

### VI. Simplicity & Operability
Prefer simple, observable designs.
- Structured logging and `/health` endpoints are mandatory.
- Config via environment variables; no hardcoded secrets.
- Keep agents decoupled and small; only shared code belongs in shared modules.

## Additional Constraints

- Providers: Gemini (Agents 1,6) and Gemini2/Groq-compatible (Agents 2–5) configured via `.env`.
- Contracts live in FastAPI/Pydantic; any change requires explicit changelog notes.
- Rate limits, retries, and graceful degradation MUST be implemented where applicable.
- Swagger docs MUST pass validation; example payloads maintained per agent.

## Development Workflow

1. Speckit flow: feature spec → implementation plan → tasks.
2. Update API contracts and provide migration notes if changed.
3. Maintain golden test data and saved responses for each agent.
4. End-to-end chain: Channel audit → Title/thumbnail audit → Script → Scenes → Ideas → Roadmap.
5. Frontend PRs must validate against backend contracts and golden examples.

## Governance
This constitution supersedes ad-hoc practices; all PRs must show compliance.
- Versioning policy: MAJOR (breaking governance), MINOR (new principle/section), PATCH (clarification).
- Compliance review: PR description MUST link affected principles and evidence (tests, contracts, examples).
- Amendments require Sync Impact Report and propagation to Speckit templates and docs.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE) | **Last Amended**: 2025-11-04
