# Unified Species Database Schema (Offline-First)

This document defines a **single, extensible database schema** for plants, fungi, terrestrial animals, and aquatic animals (fish), designed for **offline use**, **regional ML models**, and **state-based regulation packs**.

Design goals:

* One canonical taxonomic core
* Domain-specific extensions per organism type
* Explicit handling of risk, toxicity, and misidentification
* Regulations isolated into updateable state modules
* Legally conservative and defensible structure

---

## 1. Core Taxonomy (All Organisms)

### `taxon`

Canonical biological unit (species, genus, or species-complex).

* `taxon_id` (PK)
* `rank` (species | genus | complex)
* `scientific_name`
* `author_citation` (optional)
* `common_name_primary`
* `name_normalized`
* `kingdom` (Plantae | Fungi | Animalia)
* `phylum`
* `class`
* `order`
* `family`
* `genus`
* `native_status` (native | introduced | invasive | unknown)
* `conservation_status_code` (IUCN or local equivalent)
* `notes_general`

---

### `taxon_common_name`

* `taxon_common_name_id` (PK)
* `taxon_id` (FK)
* `common_name`
* `locale` (e.g. en-US)
* `region_code` (optional)

---

### `taxon_media`

* `media_id` (PK)
* `taxon_id` (FK)
* `media_type` (image | icon)
* `asset_key`
* `caption`
* `license_code`

---

## 2. Features & Identification

### `feature`

Reusable descriptive units.

* `feature_id` (PK)
* `feature_type` (morphology | behavior | habitat | track_sign | phenology | warning)
* `title`
* `description`
* `severity` (0–5)

### `taxon_feature`

* `taxon_id` (FK)
* `feature_id` (FK)
* `priority`
* `confidence_hint` (diagnostic | supporting)

---

### `lookalike_relation`

Directional lookalike mapping.

* `lookalike_id` (PK)
* `taxon_id` (FK)
* `lookalike_taxon_id` (FK)
* `risk_if_confused` (low | medium | high | extreme)
* `differentiators`
* `notes`

---

## 3. Hazards, Toxicity, and First Aid

### `hazard`

Normalized risk concept.

* `hazard_id` (PK)
* `hazard_type` (toxin | venom | irritant | pathogen | mechanical | allergen | psychoactive)
* `name`
* `summary`
* `severity` (0–5)
* `onset_notes`
* `first_aid_overview`
* `sources_note`

### `taxon_hazard`

* `taxon_id` (FK)
* `hazard_id` (FK)
* `exposure_route` (touch | ingestion | inhalation | puncture | bite)
* `risk_level` (low | medium | high | extreme)
* `precautions`
* `notes`

---

## 4. Edibility & Uses (Shared)

### `edibility_profile`

* `taxon_id` (PK/FK)
* `edibility_status` (edible | conditionally_edible | not_recommended | toxic | unknown)
* `conservatism_level` (strict | moderate)
* `notes`
* `preparation_warnings`
* `misidentification_risk_flag` (bool)

---

### `use_case`

* `use_case_id` (PK)
* `use_type` (medicinal | other)
* `title`
* `description`
* `evidence_level` (traditional | limited | moderate | strong | unknown)
* `contraindications`

### `taxon_use_case`

* `taxon_id` (FK)
* `use_case_id` (FK)
* `notes`

---

## 5. Plant Extension

### `plant_profile`

* `taxon_id` (PK/FK)
* `growth_form` (tree | shrub | forb | grass | vine | fern | moss)
* `life_cycle` (annual | biennial | perennial)
* `key_distinguishers`
* `habitat_summary`
* `toxicity_summary`
* `lookalike_warning_flag`

---

### `phenology_event`

* `phenology_event_id` (PK)
* `event_type` (flowering | fruiting | senescence)
* `description`

### `taxon_phenology`

* `taxon_id` (FK)
* `phenology_event_id` (FK)
* `start_month`
* `end_month`
* `region_code`

---

## 6. Fungi Extension

### `fungus_profile`

* `taxon_id` (PK/FK)
* `guild` (saprotrophic | mycorrhizal | parasitic)
* `substrate`
* `key_distinguishers`
* `spore_print_color`
* `toxicity_summary`
* `edibility_policy_note`

### `fungi_lookalike_rule`

* `taxon_id` (PK/FK)
* `allowed_as_edible_only_if_no_lookalikes` (bool)
* `reason`

---

## 7. Terrestrial Animal Extension

### `animal_profile`

* `taxon_id` (PK/FK)
* `animal_group` (mammal | bird | reptile | amphibian | insect | arachnid)
* `danger_level` (low | medium | high | extreme)
* `behavior_notes`
* `deterrents_overview`
* `human_conflict_mitigation`
* `habitat_summary`
* `tracks_signs_summary`

---

### `track_sign`

* `track_sign_id` (PK)
* `type` (track | scat | scrape | nest | call)
* `description`
* `media_asset_key`

### `taxon_track_sign`

* `taxon_id` (FK)
* `track_sign_id` (FK)
* `diagnostic_level` (high | medium | low)

---

## 8. Aquatic Animals (Fish) Extension

### `aquatic_profile`

* `taxon_id` (PK/FK)
* `water_type` (fresh | salt | brackish | anadromous)
* `habitat_type` (river | lake | estuary | reef | pelagic | benthic)
* `depth_range_min_m`
* `depth_range_max_m`
* `spawning_notes`
* `migration_notes`
* `key_id_markers`
* `typical_size_min_cm`
* `typical_size_max_cm`
* `consumption_risks_summary`

---

## 9. Fishing Regulations (State Packs)

### `jurisdiction`

* `jurisdiction_id` (PK)
* `type` (state | province)
* `code` (e.g. WA)
* `name`

---

### `reg_pack`

* `reg_pack_id` (PK)
* `jurisdiction_id` (FK)
* `version`
* `effective_start_date`
* `effective_end_date`
* `last_verified_date`
* `source_agency_name`
* `source_doc_title`
* `source_doc_url`
* `disclaimer_short`
* `hash`

---

### `gear_type`

* `gear_type_id` (PK)
* `name`
* `description`

---

### `waterbody` (Optional)

* `waterbody_id` (PK)
* `jurisdiction_id` (FK)
* `name`
* `type`
* `geo_hint`

---

### `reg_rule`

* `reg_rule_id` (PK)
* `reg_pack_id` (FK)
* `taxon_id` (FK)
* `scope` (statewide | waterbody_specific)
* `waterbody_id` (nullable FK)
* `season_start`
* `season_end`
* `bag_limit_daily`
* `possession_limit`
* `size_min_cm`
* `size_max_cm`
* `slot_min_cm`
* `slot_max_cm`
* `catch_and_release_only` (bool)
* `special_rules_text`
* `regulatory_confidence` (high | medium | low)
* `verification_required` (bool)

---

### `reg_rule_gear`

* `reg_rule_id` (FK)
* `gear_type_id` (FK)
* `is_allowed` (bool)
* `notes`

---

## 10. Search, UX, and Safety Helpers

### `synonym`

* `synonym_id` (PK)
* `taxon_id` (FK)
* `synonym_name`
* `type` (scientific | deprecated_common)

---

### `tag`

* `tag_id` (PK)
* `name` (e.g. invasive, protected, highly_toxic)

### `taxon_tag`

* `taxon_id` (FK)
* `tag_id` (FK)

---

### `content_warning`

* `warning_id` (PK)
* `code` (VERIFY_REGS, DO_NOT_CONSUME_IF_UNCERTAIN)
* `text`

### `taxon_warning`

* `taxon_id` (FK)
* `warning_id` (FK)
* `condition`

---

## 11. Packaging Strategy

* **Base DB**: taxonomy, biology, hazards, edibility, uses
* **State DBs**: fishing regulations only (`reg_pack`, `reg_rule`, `gear`, `waterbody`)
* Enables targeted updates and minimal legal exposure

---

This schema is intentionally conservative, modular, and designed to align with confidence-gated ML identification and offline-first deployment.
