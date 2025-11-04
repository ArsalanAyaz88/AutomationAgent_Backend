# Tasks: YouTube Automation Core (6-Agent Pipeline)

**Branch**: `001-youtube-automation-core` | **Spec**: ./spec.md | **Plan**: ./plan.md

## Task Groups (by agents)

### Agent 1: Channel Auditor
- Define request/response Pydantic models.
- Validate endpoint `POST /api/agent1/audit-channel` example payloads.
- Persist output to saved-responses with ID.
- Add minimal golden example (2 channels) + curl snippet in README.

### Agent 2: Title/Thumbnail/Hook Auditor
- Define schemas capturing: title patterns, hooks, keywords, thumbnail text/texture/placement.
- Implement endpoint `POST /api/agent2/audit-titles` with example payload.
- Ensure outputs cite evidence IDs; persist to saved-responses.
- Golden example with 2–3 video URLs.

### Agent 3: Script Generator
- Enforce mapping back to Agent 2 insights with citations.
- Implement endpoint `POST /api/agent3/generate-script` with example payload.
- Persist to saved-responses; add golden example.

### Agent 4: Script → Scene Prompts
- Deterministic scene boundaries; include camera/angle prompts.
- Implement endpoint `POST /api/agent4/script-to-prompts` with example payload.
- Persist to saved-responses; golden example script → 4–6 scenes.

### Agent 5: Ideas (Titles + Thumbnails)
- Generate 3 titles + 3 thumbnail ideas with rationale referencing data.
- Implement endpoint `POST /api/agent5/generate-ideas` with example payload.
- Persist to saved-responses; golden example.

### Agent 6: 30-Video Roadmap
- Produce 30 roadmap items with 3 title and 3 thumbnail options each.
- Implement endpoint `POST /api/agent6/generate-roadmap` with example payload.
- Persist to saved-responses; golden example with 5 items for CI.

## Cross-Cutting Tasks
- Add/verify Swagger examples per endpoint.
- Add `/health` and structured logging checks if missing.
- Add retry/backoff wrappers for provider calls.
- Ensure `.env` keys and model names align with constitution.
- Frontend service stubs for each endpoint with minimal UI smoke.

## Definition of Done
- All endpoints return schema-valid responses and render in Swagger.
- Golden examples committed and pass CI (fast, deterministic).
- Saved-responses can create/read/update/delete artifacts from each agent.
- End-to-end example documented in Backend README.

## Links
- Constitution: ../../.specify/memory/constitution.md
- Spec: ./spec.md
- Plan: ./plan.md
