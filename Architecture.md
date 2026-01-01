# FieldSense Edge AI Species ID — Liability-Optimized MVP

## Design Goals

* **Minimize user harm** from misidentification (especially **fungi**, **toxic plants**, **dangerous animals**, **harvest legality**).
* **Default to abstention** when uncertainty or input quality is high-risk.
* **Offline-first** for core identification + safety info.
* **Fast, reliable UX** on mid-tier devices (avoid heavy live pipelines).

## MVP Non-Negotiables

* **3-state outcome**: `REJECT (bad photo)` → `ABSTAIN (ambiguous)` → `ID (confident)`.
* **No edibility claims shown unless confidence + policy gates pass**.
* **Fungi edibility policy**: only show “edible” when **no dangerous lookalikes in-region** *and* confidence gates pass.
* **Regulations are versioned** with visible freshness status; never silently present stale regs as current.
* **Local-only logging by default**; explicit opt-in required for any upload/sync.

---

## MVP Scope

### Identification Modes (user selects)

* `PLANT`
* `FUNGI`
* `ANIMAL` (terrestrial)
* `FISH` (aquatic)

### Geographic Scope

* Single initial region (e.g., **Washington State**) to reduce label confusion and regulatory complexity.

---

## MVP On-Device Models

### 1) Usability / Quality Triage Model (tiny)

Purpose: classify captured image as `usable` vs `unusable`.

* Trained on a **hand-curated** dataset representative of real field conditions.
* Bias toward **false rejects** (prefer rejection over risky ID).

### 2) Regional Species Classifier (production)

Purpose: predict species probabilities for in-distribution classes.

* **Single-head** species classification for MVP (avoid dual-head leakage in early stages).
* Supports **abstention** via calibrated thresholds.

> Note: Dual-head can come later if you can prove it doesn’t learn species-frequency shortcuts.

---

## MVP Inference Pipeline

### Step 0 — Mode selection

User selects one of: Plant / Fungi / Animal / Fish.

* Store as `mode`.
* Show brief mode-specific capture guidance (1 screen, not a lecture).

### Step 1 — Lightweight Viewfinder Guidance (no MobileSAM)

Goal: improve capture quality without heavy compute.

* Run **cheap frame sampling** at low frequency (e.g., 3–5 fps equivalent), using:

  * **Sharpness**: Laplacian variance
  * **Exposure**: mean luminance + clipped blacks/whites
  * **Motion**: gyro variance (adaptive thresholds; don’t hard-fail shaky conditions)
  * **Subject centering (optional)**: center-weighted edge density (avoid saliency nets in MVP)

UI:

* Indicator: `Poor / OK / Good` with 1–2 actionable hints (e.g., “move closer”, “more light”).
* **Manual capture only** in MVP (auto-capture later).

### Step 2 — Post-capture Quality Gate (fast + strict)

Run in order:

1. **Triage model** → if `unusable`: return `REJECT`.
2. **Simple crop heuristic** (no segmentation):

   * center crop + resize OR
   * bounding box from edge-density peak (optional)

If `REJECT`:

* Prompt retake with a specific reason (blur / dark / glare / too far).

### Step 3 — Species prediction + Abstention

Run production classifier and compute:

* `top1_prob`, `top2_prob`, `margin = top1_prob - top2_prob`
* `entropy` (optional)

Decision:

* If `top1_prob < P_min[mode]` OR `margin < M_min[mode]` → return `ABSTAIN`.
* Else → return `ID` with `top1`.

Mode-specific conservative defaults (tune with validation):

* **Fungi**: highest thresholds (most abstain)
* **Plant**: high thresholds
* **Animal/Fish**: moderate thresholds

### Step 4 — Safety + Liability Policy Gate (before showing “edible” / “safe”)

Even after `ID`, apply a **policy layer** driven by the local database:

For the predicted species, fetch:

* `risk_level` (low/med/high)
* `has_dangerous_lookalikes_in_region`
* `edibility_confidence_allowed` (boolean, curated)
* `venom/danger flags`

Rules:

* If `risk_level == high` → show ID but **lead with safety warning** and emphasize confirmation steps.
* If `mode == FUNGI` and (`has_dangerous_lookalikes_in_region == true` OR `edibility_confidence_allowed == false`) → never show “edible”.
* If edible is allowed but lookalikes exist (non-dangerous): show **“possible edible — confirm with these traits”** and still allow abstention fallback.

Output states:

* `ID_ONLY` (name + traits, no edibility)
* `ID_PLUS_EDIBILITY` (rare; only for strict cases)

### Step 5 — Show lookalike comparisons (MVP-lite)

* If lookalikes exist: show a short list of **distinguishing features** (text-first).
* Images for side-by-side comparisons are **optional** in MVP (ship later).

---

## MVP Database (Offline)

### Core tables (minimum viable)

* `species`

  * `species_id`, `latin_name`, `common_name`, `mode`, `region_id`
* `risk_profile`

  * `species_id`, `risk_level`, `toxicity_summary`, `first_aid_summary`, `danger_notes`
* `lookalikes`

  * `species_id`, `lookalike_species_id`, `dangerous` (bool), `distinguishing_features`
* `regulations`

  * `region_id`, `species_id` (nullable if general), `season_dates`, `bag_limits`, `gear_rules`, `source`, `version`, `effective_date`, `retrieved_date`, `expiry_date`
* `phenology` (plants/fungi)

  * `species_id`, `months_active`, `habitat_notes`

> Keep it text-heavy in MVP. Photos and rich media can be phased in.

---

## Browse Feature (MVP)

Browse is not just a feature; it’s the **fallback path**.

* Filter by:

  * `mode`
  * `risk_level`
  * `edibility_allowed` (plants/fungi)
  * `season/phenology` (month)
  * `habitat`
* If pipeline returns `ABSTAIN`, automatically suggest:

  * “Likely candidates this month in your area” (based on region + phenology)

---

## Logging (Local Only by Default)

### What gets logged

* `timestamp`
* `mode`
* `result_state` (REJECT/ABSTAIN/ID)
* If ID: `species_id`, `confidence_band` (e.g., High/Med)
* `location` (optional; off by default)

### Location privacy

* If user enables location logging:

  * store rounded coordinates (grid) by default
  * allow “precise mode” toggle
* Provide:

  * export
  * bulk delete

---

## Regulatory Updates (MVP)

* Regulations ship with the app as a **versioned bundle** per region.
* App checks for updates when online:

  * fetch `latest_version_manifest`
  * download delta bundle
* UI must show freshness:

  * “Regs updated: YYYY-MM-DD”
  * if `now > expiry_date` → warning banner + disable “legal guidance” claims until refreshed

---

## Minimum Telemetry (Optional, Opt-in)

If user opts in:

* Upload only:

  * anonymized outcome stats (REJECT/ABSTAIN/ID rates)
  * per-species confusion info (no images unless explicitly consented)

Avoid uploading GPS + photos by default; treat as a separate, explicit feature.

---

## MVP Acceptance Criteria

* Median end-to-end time (capture → result): **< 1.5s** on mid-tier devices (excluding retakes)
* Abstention behavior:

  * Fungi: high abstain rate is acceptable (safety > coverage)
  * Plants: moderate abstain rate
* Demonstrable safeguards:

  * No edibility shown for fungi with dangerous lookalikes
  * Regulations show visible freshness and fail closed when stale
  * Local-only logging default

---

## MVP Phase-2 Upgrades (Not in MVP)

* Auto-capture
* MobileSAM segmentation post-capture
* Side-by-side lookalike image comparisons
* Dual-head production model (only after leakage testing)
* Personalized “common species near you” suggestions
