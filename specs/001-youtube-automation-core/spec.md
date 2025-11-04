# Feature Spec: YouTube Automation Core (6-Agent Pipeline)

**Branch**: `001-youtube-automation-core`  
**Owner**: Platform  
**Constitution Alignment**: Data-Driven, API-First, Testable Outcomes, Reproducibility, Responsible AI, Operability  

## Summary
Implement and document the end-to-end, API-first workflow across 6 agents:
1) Channel audit. 2) Title/thumbnail/keywords/hooks audit. 3) Script generation.
4) Script→scene prompts with angles/directing. 5) 3 winning titles and thumbnail ideas.
6) 30-video roadmap with 3 titles and 3 thumbnails each. Persist artifacts to MongoDB saved-responses.

## Goals & Non-Goals
- Goals: Stable contracts for all 6 endpoints, measurable outputs, saved-responses integration, example payloads, alignment with Next.js frontend.
- Non-Goals: Implement video rendering, external scraping beyond official APIs, paid provider billing configuration.

## User Stories
- As a creator, I want the system to pick the best competitor channel so I can model winning content (Agent 1).
- As a strategist, I want to extract title/thumbnail patterns and hooks so I can drive CTR (Agent 2).
- As a writer, I want a script grounded in the patterns so it retains viewers (Agent 3).
- As a director, I want scene-by-scene prompts to guide visuals and camera movement (Agent 4).
- As a growth lead, I want 3 winning titles and thumbnail ideas per topic (Agent 5).
- As a planner, I want a 30-video roadmap with variations to schedule content (Agent 6).

## API Contracts (FastAPI)
- POST `/api/agent1/audit-channel`
  - Request: `{ channel_urls: string[], user_query?: string }`
  - Response: `{ best_channel: {...}, reasons: string[], evidence_ids: string[], saved_response_id?: string }`
- POST `/api/agent2/audit-titles`
  - Request: `{ video_urls: string[] }`
  - Response: `{ patterns: {...}, hooks: {...}, keywords: string[], thumbnail_findings: {...}, evidence_ids: string[], saved_response_id?: string }`
- POST `/api/agent3/generate-script`
  - Request: `{ title_audit_data: string|object, topic: string }`
  - Response: `{ script: string, citations: string[], saved_response_id?: string }`
- POST `/api/agent4/script-to-prompts`
  - Request: `{ script: string }`
  - Response: `{ scenes: [{id:number, boundary:string, angle:string, prompt:string}], saved_response_id?: string }`
- POST `/api/agent5/generate-ideas`
  - Request: `{ winning_videos_data: string|object }`
  - Response: `{ titles: string[3], thumbnails: string[3], rationale: string[], saved_response_id?: string }`
- POST `/api/agent6/generate-roadmap`
  - Request: `{ niche: string, winning_data?: string|object }`
  - Response: `{ items: [{titleOptions:string[3], thumbnailOptions:string[3]}] (len=30), saved_response_id?: string }`

Note: Each response MUST be stored/serializable in MongoDB saved-responses API already implemented: GET/POST/PUT/DELETE `/api/saved-responses/...`.

## Data Flow
Agent1 → Agent2 → Agent3 → Agent4 → Agent5 → Agent6. Persist each step; downstream steps cite upstream evidence IDs.

## Validation & Metrics
- Agent2 detects patterns for: title structure, keyword placement, hook type, thumbnail text/texture/placement.
- Agent4 scenes have deterministic boundaries and include angle/camera guidance.
- Agent5/6 provide rationales linked to Agent2 findings.

## Non-Functional Requirements
- Contracts validated by Swagger `/docs`.
- Structured logging and `/health` return healthy.
- Rate limit/backoff for external calls.

## Acceptance Criteria
- All 6 endpoints return schema-valid responses and example payloads.
- Saved-response entries are created and retrievable.
- Example E2E run with minimal payloads documented.

## Risks
- Provider quota/latency; mitigated with retries/backoff and clear error messages.
- Data drift in YouTube pages; rely on official APIs/tools.

## Open Questions
- RATIFICATION_DATE for constitution.
