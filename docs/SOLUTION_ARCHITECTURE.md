# MomentoCards (Momenta Brand AI) — Solution Architecture

## 1. Overview

MomentoCards is a multi-tenant SaaS backend for AI-generated brand creative —
not just calendars, but the full Canva-style deliverable taxonomy (flyers,
brochures, invitations, certificates, social posts, catalogs, etc.). A
customer onboards a **Brand**, optionally trains a **custom LoRA** on their
own reference imagery, and runs a guided **Campaign** workflow
(Goal → Layout → Content → Preview → Audience → Generate → Review → Launch)
that ends in one or more generated, brand-governed creative assets.

**Stack**: Python / FastAPI / SQLAlchemy (SQLite today, swappable to Postgres
via `DATABASE_URL`), Replicate as the generation provider, a Next.js
frontend consuming the REST API.

```
                        +-----------------+
                        |  Next.js Web    |
                        +--------+--------+
                                 |  REST (fetch)
                                 v
                        +-----------------+
                        |  FastAPI app    |
                        |  (app/main.py)  |
                        +--------+--------+
                                 |
        +------------------------+------------------------+
        |                        |                        |
        v                        v                        v
 +-------------+         +----------------+        +----------------+
 | Brand Engine|         | Campaign       |        | Deliverable /  |
 | (brands,    |         | Workflow       |        | Generation API |
 | rules,      |         | (8-stage state |        | (deliverables, |
 | orgs)       |         | machine)       |        | training, video)|
 +------+------+         +-------+--------+        +-------+--------+
        |                        |                          |
        v                        v                          v
 +----------------------------------------------------------------+
 |                     SQLAlchemy models / SQLite                  |
 +----------------------------------------------------------------+
                                 |
                                 v
                  +--------------------------+
                  | Replicate Client          |
                  | (training / predictions / |
                  |  webhooks)                 |
                  +-------------+--------------+
                                 |
                                 v
                  +--------------------------+
                  | App-owned storage          |
                  | (/storage/{assets,grids,  |
                  |  outputs})                 |
                  +--------------------------+
```

## 2. Subsystems

### 2.1 Brand Engine (`app/api/brands.py`, `brand_rules.py`, `organizations.py`)
- **Organization** → **Brand** (lightweight multi-tenancy; auth/membership
  enforcement not yet wired).
- **Brand Knowledge**: `primary_color`, `secondary_color`, `mood_keywords`,
  `industry`, `voice`, `fonts`, `logo_asset_id` — the structured brand
  metadata consumed by prompt-building and governance.
- **BrandAsset**: uploaded reference images (used for LoRA training and as
  IP-Adapter reference); auto-zipped for training via `services/storage.py`.
- **Brand Governance** (`services/governance.py` + `BrandRule`): rules
  (`logo_mandatory`, `forbidden_fonts`, `min_primary_color_usage`) validated
  as a hard gate before a campaign can reach Launch.

### 2.2 LoRA / Training System (`app/api/training.py`, `lora_presets.py`, `services/training_service.py`)
- **Per-brand private LoRA** (`LoraModel`): trained from ≥10 uploaded
  reference images via Replicate's training API; categorized by
  `LoraCategory` (branding / typography / locale / community / subject).
- **Automatic training trigger**: crossing `AUTO_TRAIN_ASSET_THRESHOLD`
  uploaded assets auto-starts a branding LoRA run (no manual call needed).
- **SharedLoraPreset**: platform-owned LoRAs (e.g. a "Tamil Nadu locale" or
  "temple architecture" preset) usable across any brand, same category
  matrix as private LoRAs.
- `weights_url` is **never** returned to the client on either entity — only
  the `id`/`status`/`is_ready` needed to select it in generation.

### 2.3 Template Intelligence (`app/api/templates.py`, `services/template_service.py`)
- **Template**: a named, pre-built layout (category + tags + seed
  `canvas_json`) scoped to a `DocumentType`.
- Retrieval today is deterministic keyword/category matching
  (`find_best_template`); offered as an *advisory* suggestion during the
  Layout stage. Written so an embedding/vector-search upgrade (Template RAG)
  can replace the function body without touching callers.

### 2.4 Document Taxonomy (`app/api/document_types.py`, `services/document_catalog.py`)
- **DocumentType**: seeded catalog entry per deliverable kind (wall
  calendar, tri-fold brochure, flyer, certificate, ...), carrying
  `layout_kind` (single_sheet / folded / multi_page / grid / micro / live),
  `default_page_count`, `requires_grid`, and `fulfillment_options`.
- This is the taxonomy layer the rest of the system is generalized against —
  calendars are one `layout_kind=grid` entry among many, not a special case.

### 2.5 Deliverable / Generation Engine (`app/api/deliverables.py`, `services/deliverable_service.py`, `services/grid_generator.py`, `services/prompt_builder.py`, `services/replicate_client.py`)
- **Deliverable** owns N **DeliverablePage**s (e.g. 12 for a wall calendar, 1
  for a flyer).
- Chains, per page: code-generated grid + Canny edge map (ControlNet, grid
  layouts only) + brand/preset LoRA weights + IP-Adapter reference image +
  built prompt/negative-prompt into a single Replicate prediction.
- **Video** (`services/video_service.py`): img2vid from an already-succeeded
  page's image as keyframe, via a second Replicate prediction.
- **Status sync**: dual-path — `GET /deliverables/{id}` polls Replicate, and
  `POST /webhooks/replicate` (idempotent via `WebhookEvent`) pushes
  completion when `APP_BASE_URL` is configured.
- **App-owned storage**: every successful provider output is downloaded into
  `/storage/outputs/` immediately (`storage.persist_provider_output`) — the
  raw, temporary Replicate URL is never persisted or returned.

### 2.6 Campaign Workflow (`app/api/campaigns.py`, `services/workflow/*`)
Strict forward-only state machine (`stages.require_stage` / `advance_to`),
one explicit backward exception (Review reject → Content):

```
Goal → Layout → Content → Preview → Audience → Generate → Review → Launch → Done
```
- **Goal**: free-text goal + intent.
- **Layout**: picks DocumentType (+ grid params if required) and optional
  brand LoRA; surfaces a suggested Template.
- **Content**: text fields + uploaded photos (`CampaignAsset`).
- **Preview**: fabric.js canvas JSON saved/approved (pre-generation mockup).
- **Audience**: adaptive clarifying Q&A.
- **Generate**: creates the actual `Deliverable` via the shared
  `deliverable_service.create_deliverable`.
- **Review**: WYSIWYG final-canvas save (fabric.js, seeded with the
  generated image) — hard-gates Launch until saved + approved.
- **Launch**: re-checks deliverable completion, final-canvas approval, **and
  Brand Governance** before marking the campaign Done; returns the
  app-owned output URLs (digital_export only — print/live-publish are
  modeled via `FulfillmentType` but not implemented).

### 2.7 Frontend (`web/`)
- Next.js (App Router) + Tailwind + fabric.js, talking to the FastAPI API
  via `src/lib/api.ts` (typed fetch client, one function per endpoint).
- Scaffolded; page-level UI (brand/org management, LoRA upload+train,
  campaign wizard, fabric.js preview/final-canvas editor, generation history
  with polling) is the active build-out track.

## 3. Data Model Summary

| Entity | Purpose |
|---|---|
| `Organization` | Tenant boundary (foundation only, no auth enforcement yet) |
| `Brand` | Identity: colors, mood, industry, voice, fonts, logo |
| `BrandAsset` | Uploaded reference image (training / IP-Adapter / logo) |
| `BrandRule` | Governance constraint, validated at Launch |
| `LoraModel` | Brand-private trained LoRA |
| `SharedLoraPreset` | Platform-owned LoRA, reusable across brands |
| `DocumentType` | Deliverable taxonomy entry (seeded, not user-created) |
| `Template` | Pre-built layout suggestion within a DocumentType |
| `Deliverable` / `DeliverablePage` | One generation job / one page-level prediction |
| `Campaign` | Workflow instance, one JSON blob per stage |
| `CampaignAsset` | Content-stage photo upload |
| `WebhookEvent` | Idempotency ledger for Replicate webhook delivery |

## 4. Cross-Cutting Constraints (enforced, not aspirational)

- **No raw provider exposure**: LoRA `weights_url` and Replicate's temporary
  output URLs never reach the client — only app-issued ids/paths do.
- **Idempotent webhooks**: `WebhookEvent.provider_prediction_id` is unique;
  duplicate Replicate deliveries are a no-op.
- **App-owned storage over trusting provider URLs**: every output is
  downloaded locally before being referenced anywhere in a response.
- **Provider-swappable boundary**: all Replicate calls are isolated in
  `services/replicate_client.py`; everything else talks to it through plain
  Python functions, not the SDK directly.
- **Forward-only workflow**: campaign stage transitions are enforced in one
  place (`workflow/stages.py`), preventing skipped/duplicated steps.
- **Brand governance as a hard gate**: violations block Launch outright
  rather than just warning.

## 5. Deferred (flagged, not silently dropped)

- **Brand/Template RAG**: embedding-based vector search (Qdrant or
  similar) — today's retrieval is deterministic keyword/category matching by
  design, with a clean seam to swap in (`template_service.find_best_template`).
- **AI-assisted canvas edits** ("move logo left", "translate to Tamil") —
  canvas stages currently accept only direct `canvas_json` saves.
- **Print-safe guides / PDF export / brand-lock canvas regions.**
- **Multi-provider Model Router** (FLUX vs. SDXL vs. Firefly) — one
  Replicate model per task type is hardcoded via `core/config.py` today.
- **Auto-caption generation** (Florence-2/BLIP-2) for training images —
  trigger words are a fixed string, not derived from image content.
- **Full multi-tenant auth/membership enforcement** on top of the
  `Organization` → `Brand` data boundary.
