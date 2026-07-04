# CRUD API Design

## Goal

Support M4 by defining a small, testable API contract for creating, editing, and deleting jobs before adding iOS CRUD UI.

## Current State

- `GET /api/jobs` returns jobs from the latest generated report.
- `GET /api/latest-report` returns the latest report payload.
- There is no mutable job store yet.
- There are no `POST`, `PUT`, or `DELETE` handlers yet.

## Persistence Decision Needed

Vercel serverless functions should not write durable application state to the repo filesystem. Before implementing CRUD, choose one durable store:

1. **External database**: preferred for production CRUD.
   - Examples: Vercel Postgres, Supabase, Neon, Firebase.
   - Supports concurrent users and durable updates.
2. **File-based JSON store**: acceptable only for local development or demos.
   - Not reliable on Vercel serverless.
   - Should not be treated as production persistence.

Recommended path: use an external database and keep report-generated jobs read-only unless they are imported into the mutable store.

## Job Resource Shape

```json
{
  "id": "uuid-string",
  "title": "Senior Security Engineer",
  "company": "Tencent",
  "location": "Beijing",
  "url": "https://careers.tencent.com/job/123",
  "score": 2,
  "summary": "",
  "source": "",
  "publishedDate": null,
  "salaryRange": "40-65K"
}
```

Compatibility note: read endpoints may continue accepting legacy `salary`; write endpoints should normalize to `salaryRange`.

## Proposed Endpoints

### `GET /api/jobs`

Returns all jobs visible to the app.

Response:

```json
[
  { "id": "...", "title": "...", "company": "..." }
]
```

### `POST /api/jobs`

Creates a job.

Request body:

```json
{
  "title": "Senior Security Engineer",
  "company": "Tencent",
  "location": "Beijing",
  "url": "https://careers.tencent.com/job/123",
  "score": 2,
  "summary": "",
  "source": "manual",
  "publishedDate": "2026-07-01",
  "salaryRange": "40-65K"
}
```

Response: `201 Created`

```json
{
  "id": "generated-uuid",
  "title": "Senior Security Engineer",
  "company": "Tencent",
  "location": "Beijing",
  "url": "https://careers.tencent.com/job/123",
  "score": 2,
  "summary": "",
  "source": "manual",
  "publishedDate": "2026-07-01",
  "salaryRange": "40-65K"
}
```

### `PUT /api/jobs/{id}`

Replaces an existing job.

Response: `200 OK` with the updated job, or `404 Not Found`.

### `DELETE /api/jobs/{id}`

Deletes an existing job.

Response: `204 No Content`, or `404 Not Found`.

## Validation Rules

Required fields:

- `title`
- `company`
- `location`
- `url`
- `score`

Rules:

- `score` must be an integer.
- `url` must be non-empty and should be URL-shaped.
- Optional string fields default to empty string or `null` consistently with the iOS model.

## Test Plan

Backend tests:

1. `GET /api/jobs` returns a list of normalized jobs.
2. `POST /api/jobs` creates a job and generates an `id`.
3. `POST /api/jobs` rejects missing required fields.
4. `PUT /api/jobs/{id}` updates an existing job.
5. `PUT /api/jobs/{id}` returns `404` for unknown ids.
6. `DELETE /api/jobs/{id}` removes a job.
7. `DELETE /api/jobs/{id}` returns `404` for unknown ids.

iOS tests:

1. `Job` decodes backend-compatible payloads.
2. `Job` encodes write payloads with `salaryRange`.
3. API service methods use the expected HTTP methods and paths.

## Implementation Order

1. Choose durable persistence.
2. Add backend storage adapter behind a small interface.
3. Add backend CRUD handlers and tests.
4. Add iOS `APIService` create/update/delete methods.
5. Add iOS view model state updates.
6. Add add/edit/delete UI.
7. Verify on CI and simulator.
