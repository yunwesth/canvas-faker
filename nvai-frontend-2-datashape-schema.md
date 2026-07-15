# nvai-frontend-2 — Required Datashape Schema

**Target:** `nv-live-frontend-2` (React + Vite + TypeScript) — the container running on port **6767**.
**Source examined:** `dgx-spark-stacks/infrastructure/nv-live/frontend/src/` (`types.ts`, `api/*.ts`, hooks, components).
**Purpose:** Defines the exact data contract the backend must satisfy for the frontend to function. This is derived from what the frontend *consumes*, so it is the authoritative "sufficient to function" spec regardless of backend internals.