# Implementation Plan: YouTube Automation Core (6-Agent Pipeline)

**Branch**: `001-youtube-automation-core` | **Date**: 2025-11-04 | **Spec**: ./spec.md
**Input**: Feature specification for the 6-agent end-to-end workflow

## Summary
Deliver a stable, API-first implementation and documentation pass across all 6 agents with
schema-validated endpoints, persisted artifacts (saved-responses), and minimal golden examples.

## Technical Context

**Language/Version**: Python 3.12 (Backend), Node 18+/Next.js 15 (Frontend)
**Primary Dependencies**: FastAPI, Pydantic, Uvicorn, MongoDB (pymongo), OpenAI SDK-compatible clients, Tailwind/React
**Storage**: MongoDB (saved responses)
**Testing**: pytest (API), Next.js test utils (basic), curl examples via Swagger
**Target Platform**: Backend service + Next.js web app
**Project Type**: Web application with backend + frontend
**Performance Goals**: Responsive API for interactive usage; typical end-to-end run < 30s with caching where possible
**Constraints**: Provider quotas, network variability; deterministic minimal examples for CI
**Scale/Scope**: Single-team project; extensible for additional agents later

## Constitution Check

- Data-Driven Strategy: Use Agent 1/2 outputs as source of truth; persist with IDs.
- API-First: Maintain Pydantic request/response schemas; `/docs` must be green.
- Testable Outcomes: Define acceptance metrics per agent; include golden examples.
- Reproducibility: Ensure re-runs reproduce outputs given same inputs; use saved-responses.
- Responsible AI: Respect YouTube API quotas and ToS; secure env vars.
- Operability: Structured logging + `/health` is mandatory.

## Project Structure

```text
specs/001-youtube-automation-core/
├── spec.md
├── plan.md
└── tasks.md

Backend/
├── main.py
├── AllAgents/
│   ├── Agent_1_ChannelAuditor/
│   ├── Agent_2_TitleAuditor/
│   ├── Agent_3_ScriptGenerator/
│   ├── Agent_4_ScriptToScene/
│   ├── Agent_5_generateIdeas/
│   └── Agent_6_roadmap/
└── tests/ (to add minimal golden examples)

frontend/
└── src/ (integrate via existing services/api clients)
```

**Structure Decision**: Web application (frontend + backend). Golden examples will live under
`Backend/tests/` and example payloads in repo docs if needed.

## Milestones

- M1: Contract audit and example payloads for all 6 endpoints
- M2: Saved-responses E2E: create, retrieve, update, delete
- M3: Golden example flows for Agents 2, 4, 6
- M4: Frontend service integration smoke test against `/docs` schemas

## Risks & Mitigations

- Provider quotas → Backoff/retry, configurable models via `.env`
- Schema drift → CI check for Swagger validity; review contract diffs
- Data drift → Keep minimal examples resilient to content changes

## Acceptance Criteria

- All endpoints return schema-valid payloads with examples.
- Mongo saved-responses can store and retrieve artifacts produced by each agent.
- One documented E2E run verified by curl or Swagger for the full chain.
