"""
Core data contracts for the Stefan & Jan content pipeline.

Design notes (see CLAUDE.md for the full rationale):

  * `EpisodeIdea` and `CritiqueResult` are the ONLY models produced directly by an
    LLM via structured outputs. Keep them small and keep their fields *required*:
    structured outputs cap optional/union params per request (24 optional / 16 union),
    and every Optional field is a union (`anyOf [..., null]`). The full `Episode` is
    assembled in Python around the generated idea and may have as many optionals as it likes.

  * Numeric/length constraints (e.g. "<= 2 motions") are NOT enforced by constrained
    decoding. The Python SDK strips them from the sent schema, folds them into the field
    description, and then validates the response against the original constraint. So a
    plain Pydantic validator is the real enforcement — write it and trust it. (ShotSpec
    is not LLM-generated in v1 anyway, so its validator runs purely client-side.)

  * Facet AXES are fixed (schema); facet VALUES are data. `econ_concept` / `location` /
    `activity` are free strings validated elsewhere against the YAML libraries;
    `gag_structure` is a small controlled vocabulary, so it is an enum.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Enums (controlled vocabularies)
# --------------------------------------------------------------------------- #

class EpisodeStatus(str, Enum):
    DRAFT = "draft"                    # generated, not yet gated
    PENDING_REVIEW = "pending_review"  # passed mechanical gates, awaiting human
    ACCEPTED = "accepted"              # human-approved -> sits in the buffer
    REJECTED = "rejected"             # human- or hard-gate-rejected
    POSTED = "posted"                 # published (later milestone)


class GagStructure(str, Enum):
    SINGLE_SCENE = "single_scene"     # one tableau, one beat
    PARALLEL_CUT = "parallel_cut"     # Stefan's version vs Jan's version, escalating
    MULTI_PANEL = "multi_panel"       # a short sequence telling one mini-story
    REACTION = "reaction"             # button / freeze-frame deadpan payoff
    ESCALATION = "escalation"         # a single situation spiralling


class ReviewVerdict(str, Enum):
    ACCEPT = "accept"
    EDIT = "edit"
    REJECT = "reject"


class GateStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"   # triage flag surfaced to the human; never blocks on its own
    FAIL = "fail"   # blocking, only for mechanical gates


class SlotMode(str, Enum):
    CHARACTER_LED = "character_led"  # ~2 in 3: pure character comedy, econ optional/absent
    CONCEPT_LED = "concept_led"      # ~1 in 3: a concept IS the episode ("Stefan Explains...")


# --------------------------------------------------------------------------- #
# Facets — the anti-repetition axes
# --------------------------------------------------------------------------- #

class Facets(BaseModel):
    """The five axes dedup tracks. Axes are fixed; values are data."""
    model_config = ConfigDict(extra="forbid")

    econ_concept: str | None = Field(default=None, description="Key into econ_concepts.yaml (e.g. 'opportunity_cost'). None for pure character-comedy beats — most beats (~2 in 3) carry no concept.")
    location: str = Field(description="Where the scene happens (e.g. 'Tunnel View', 'In-N-Out drive-thru').")
    activity: str = Field(description="What the tigers are doing (e.g. 'packing', 'lap swimming').")
    gag_structure: GagStructure
    supporting_cast: list[str] = Field(
        default_factory=list,
        description="Non-tiger plush characters present (e.g. ['hawk', 'marmot']). Empty list if none.",
    )


# --------------------------------------------------------------------------- #
# ShotSpec — defined now, UNUSED in v1 (populated when video decomposition lands)
# --------------------------------------------------------------------------- #

class ShotSpec(BaseModel):
    """One image-to-video beat. Shape is locked now so the jump to video is
    'start populating a field', not a schema migration. Nothing writes this in v1."""
    model_config = ConfigDict(extra="forbid")

    index: int
    description: str = Field(description="What the still shows for this beat.")
    camera: str = Field(default="static", description="Camera move. Keep 'static' — invented motion makes AI video wobble.")
    motions: list[str] = Field(
        default_factory=list,
        description="At most TWO small, specific motions (e.g. ['Stefan taps pointer', 'Jan's ice cream drips']).",
    )
    on_image_text: str | None = Field(default=None, description="Caption / chalkboard text, if any.")
    props: list[str] = Field(default_factory=list)
    duration_seconds: float | None = None

    @field_validator("motions")
    @classmethod
    def _at_most_two_motions(cls, v: list[str]) -> list[str]:
        if len(v) > 2:
            raise ValueError("A shot may specify at most 2 motions (AI video degrades with more).")
        return v


# --------------------------------------------------------------------------- #
# LLM-GENERATED models (keep small; keep fields required)
# --------------------------------------------------------------------------- #

class EpisodeIdea(BaseModel):
    """The reviewable unit the generator produces: the gag itself.
    Shot decomposition is a separate, later call — do not generate shots here.
    econ_concept lives ONCE, in facets (the store lifts it into an indexed column);
    it is NOT duplicated here. Most episodes (~2 in 3) have facets.econ_concept = None
    and are pure character comedy — econ is seasoning, not the meal."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Short internal handle for the episode.")
    premise: str = Field(description="The scene: what Stefan and Jan are doing and what goes right/wrong.")
    caption: str = Field(description="The deadpan punchline caption. When facets.econ_concept is set it NAMES what the image already shows (shown, not stated); otherwise it is pure character comedy.")
    facets: Facets


class CandidateSet(BaseModel):
    """Structured-output container for ONE generation call: the N diverse candidates the
    daily generator returns. Use as `output_format`; selection/gating happens downstream."""
    model_config = ConfigDict(extra="forbid")

    episodes: list[EpisodeIdea] = Field(description="The distinct candidate episodes for this slot.")


class CritiqueResult(BaseModel):
    """Output of the critic pass. Mechanical checks are booleans (drive hard gates);
    judgment checks are nullable strings (surfaced to the human as triage, never auto-reject)."""
    model_config = ConfigDict(extra="forbid")

    on_model: bool = Field(description="True if Stefan/Jan are portrayed correctly (Jan has his tag, Stefan is the competent one, etc.).")
    render_feasible: bool = Field(description="True if this can animate: static camera, <=2 motions, no dependence on legible text.")
    econ_concern: str | None = Field(default=None, description="If the econ is misused or only name-dropped, describe how. Else null.")
    humor_concern: str | None = Field(default=None, description="If the gag is weak/flat/derivative, describe why. Else null.")
    issues: list[str] = Field(default_factory=list, description="Any other concrete problems.")


# --------------------------------------------------------------------------- #
# Persisted / assembled models (Python-built; optionals are fine here)
# --------------------------------------------------------------------------- #

class GateResult(BaseModel):
    name: str
    status: GateStatus
    blocking: bool = Field(description="Mechanical gates block; triage flags do not.")
    message: str | None = None


class ReviewDecision(BaseModel):
    """The human verdict. THIS IS THE SEED OF THE FUTURE HUMOR DATASET — log it always."""
    verdict: ReviewVerdict
    edited_premise: str | None = None
    edited_punchline: str | None = None
    note: str | None = None
    reviewed_at: datetime = Field(default_factory=_utcnow)


class Provenance(BaseModel):
    """Attached to every kept episode. Cheap, and it makes 'why did it generate this'
    and reproducibility work. Cost accounting lives here too."""
    prompt_name: str
    prompt_version: str = Field(description="Short hash of the template source, so a prompt change is traceable.")
    model: str
    temperature: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    generated_at: datetime = Field(default_factory=_utcnow)


class Episode(BaseModel):
    """The full persisted object. Stored as a JSON blob in the DB with
    id / slot_id / status / econ_concept / arc_id pulled out as indexed columns."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Natural key == slot_id for standalone episodes; arc beats append a position suffix. Upsert on this for idempotency.")
    slot_id: str = Field(description="The year-plan slot this episode fills (e.g. '2026-W28-D03').")
    post_date: date | None = Field(default=None, description="Target post date. May be assigned from the buffer at posting time.")

    idea: EpisodeIdea
    shots: list[ShotSpec] = Field(default_factory=list, description="Empty in v1; populated at video-decomposition time.")

    # Arc membership (first-class travel blocks; siblings are dedup-exempt)
    arc_id: str | None = None
    arc_position: int | None = None

    # Override / news-reactive seams (wired now, behavior may come later)
    priority: int = Field(default=0, description="Higher jumps the buffer queue. Override path sets this.")
    topical: bool = Field(default=False, description="True if generated in reaction to a current event.")
    topical_context: str | None = None

    status: EpisodeStatus = EpisodeStatus.DRAFT
    gate_results: list[GateResult] = Field(default_factory=list)
    review: ReviewDecision | None = None
    provenance: Provenance | None = None

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Planning models (live in YAML as Tier-1; schemas validate them on load)
# --------------------------------------------------------------------------- #

class Arc(BaseModel):
    """A contiguous travel/theme block (a week in Yosemite, ~a week in Japan).
    Scheduled as a unit; overrides per-slot concept defaults across its span."""
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    theme: str
    location: str
    start_slot: str = Field(description="First week slot, e.g. '2026-W28'.")
    length_slots: int = Field(description="How many weeks the arc spans.")
    continuity_notes: str | None = None
    concept_sequence: list[str] = Field(
        default_factory=list,
        description="Optional per-beat econ targets; falls back to free choice within the arc theme.",
    )


class YearSlot(BaseModel):
    """One week of the annual plan: a PRIOR, hand-editable, the travel-steering lever."""
    model_config = ConfigDict(extra="forbid")

    slot_id: str = Field(description="Week key, e.g. '2026-W28'.")
    theme: str
    mode: SlotMode = Field(default=SlotMode.CHARACTER_LED, description="character_led (~2 in 3) vs concept_led (~1 in 3, the 'Stefan Explains...' register).")
    target_concept: str | None = Field(default=None, description="Econ concept this week aims to cover. Set for concept_led slots; usually None for character_led. Drives coverage top-down when present.")
    season: str | None = None
    location: str | None = None
    calendar_anchor: str | None = Field(default=None, description="Real-world hook, e.g. 'tax day', 'Black Friday'.")
    arc_id: str | None = Field(default=None, description="Set if this slot belongs to an arc block.")


class YearPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    slots: list[YearSlot]
    arcs: list[Arc] = Field(default_factory=list)
