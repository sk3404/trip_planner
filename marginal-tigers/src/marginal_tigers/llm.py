"""
The one place the pipeline talks to an LLM.

Every call: render a Jinja template -> call Claude with native structured outputs
(`messages.parse(output_format=PydanticModel)`) -> get back a validated Pydantic object
plus a `Provenance` record (tokens, cost, latency, prompt version). Nothing untyped
flows downstream; a schema violation or refusal raises rather than returning junk.

Why structured outputs and not the tool-forcing workaround: native structured outputs
are GA on Opus 4.8 / Sonnet 4.6 / Haiku 4.5 and use grammar-constrained decoding, so the
response is guaranteed schema-valid with no retry loop. The Python SDK's `messages.parse()`
accepts a Pydantic model directly as `output_format`, transforms any unsupported
constraints into description hints, and validates the result against the original model.

Control-flow note: this module does NOT make the LLM agentic. Retrieval (history, bible,
coverage) is fetched deterministically by the caller and injected as template context.
The generate -> critique -> revise loop is Python control flow in planner/daily.py, not the
model deciding its own steps. See CLAUDE.md ("don't agent-wash deterministic steps").
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

from anthropic import Anthropic
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from schemas import Provenance

T = TypeVar("T", bound=BaseModel)


# --------------------------------------------------------------------------- #
# Roles: which model / temperature each pipeline step uses (configurable, not hardcoded)
# --------------------------------------------------------------------------- #

class Role(str, Enum):
    GENERATION = "generation"  # the gags — strongest creative model
    CRITIC = "critic"          # mechanical gates + econ/humor triage — cheap, fast
    PLANNER = "planner"        # annual structure — best model, runs rarely


# Standard list pricing, USD per 1M tokens. Verified 2026-06 against
# https://platform.claude.com/docs (Opus 4.8 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5).
# This is CONFIG, not a constant of nature — when prices move, edit here (or lift into
# config.py). Batch API halves these; prompt-cache reads are ~0.1x input. Not modeled yet.
PRICING_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5-20251001": (1.00, 5.00),
}


class LLMSettings(BaseSettings):
    """Reads .env / environment. ANTHROPIC_API_KEY is picked up by the SDK directly."""
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SJ_", extra="ignore")

    prompts_dir: Path = Path("prompts")
    debug_logging: bool = False                       # log full transcripts incl. rejected candidates
    debug_log_path: Path = Path("data/llm_calls.jsonl")

    generation_model: str = "claude-opus-4-8"
    critic_model: str = "claude-haiku-4-5-20251001"
    planner_model: str = "claude-opus-4-8"

    generation_temperature: float = 1.0              # high: we want diverse gags
    critic_temperature: float = 0.2                  # low: consistent judgement
    planner_temperature: float = 0.7

    generation_max_tokens: int = 1500
    critic_max_tokens: int = 1024
    planner_max_tokens: int = 8000

    def model_for(self, role: Role) -> str:
        return getattr(self, f"{role.value}_model")

    def temperature_for(self, role: Role) -> float:
        return getattr(self, f"{role.value}_temperature")

    def max_tokens_for(self, role: Role) -> int:
        return getattr(self, f"{role.value}_max_tokens")


# --------------------------------------------------------------------------- #
# Typed failures (callers handle these explicitly; never silently degrade)
# --------------------------------------------------------------------------- #

class LLMRefusal(RuntimeError):
    """Claude returned stop_reason='refusal'; output does not match the schema."""


class LLMTruncated(RuntimeError):
    """Hit max_tokens before completing; output is incomplete. Retry with more tokens."""


@dataclass
class LLMResult[T]:
    value: T
    provenance: Provenance


# --------------------------------------------------------------------------- #
# The client
# --------------------------------------------------------------------------- #

class LLMClient:
    def __init__(self, settings: LLMSettings | None = None, client: Anthropic | None = None):
        self.settings = settings or LLMSettings()
        self._client = client or Anthropic()
        self._jinja = Environment(
            loader=FileSystemLoader(str(self.settings.prompts_dir)),
            undefined=StrictUndefined,   # fail loudly on a missing template variable
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # -- prompt rendering / versioning ------------------------------------- #

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        return self._jinja.get_template(template_name).render(**context)

    def _prompt_version(self, template_name: str) -> str:
        """Short hash of the template SOURCE, so a kept episode is traceable to the
        exact prompt that made it. Tracks the template, not the rendered instance."""
        src = (self.settings.prompts_dir / template_name).read_bytes()
        return hashlib.sha256(src).hexdigest()[:8]

    # -- the single structured call ---------------------------------------- #

    def generate(
        self,
        *,
        role: Role,
        template_name: str,
        context: dict[str, Any],
        output_model: type[T],
        system: str | None = None,
    ) -> LLMResult[T]:
        """Render `template_name` with `context`, call the model for `role`, and return
        a validated `output_model` instance plus provenance."""
        model = self.settings.model_for(role)
        temperature = self.settings.temperature_for(role)
        max_tokens = self.settings.max_tokens_for(role)

        user_prompt = self._render(template_name, context)
        kwargs: dict[str, Any] = dict(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": user_prompt}],
            output_format=output_model,   # SDK convenience: Pydantic model -> output_config.format
        )
        if system is not None:
            kwargs["system"] = system

        t0 = time.perf_counter()
        response = self._client.messages.parse(**kwargs)
        latency_ms = int((time.perf_counter() - t0) * 1000)

        stop = getattr(response, "stop_reason", None)
        if stop == "refusal":
            self._maybe_log(template_name, model, user_prompt, None, "refusal")
            raise LLMRefusal(f"{template_name} on {model} was refused.")
        if stop == "max_tokens":
            self._maybe_log(template_name, model, user_prompt, None, "max_tokens")
            raise LLMTruncated(f"{template_name} on {model} hit max_tokens ({max_tokens}).")

        parsed: T = response.parsed_output  # already validated against output_model

        usage = response.usage
        in_tok, out_tok = usage.input_tokens, usage.output_tokens
        provenance = Provenance(
            prompt_name=template_name,
            prompt_version=self._prompt_version(template_name),
            model=model,
            temperature=temperature,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=self._cost(model, in_tok, out_tok),
            latency_ms=latency_ms,
            generated_at=datetime.now(timezone.utc),
        )
        self._maybe_log(template_name, model, user_prompt, parsed, "ok", provenance)
        return LLMResult(value=parsed, provenance=provenance)

    # -- helpers ----------------------------------------------------------- #

    @staticmethod
    def _cost(model: str, in_tok: int, out_tok: int) -> float:
        in_rate, out_rate = PRICING_PER_MTOK.get(model, (0.0, 0.0))
        return (in_tok * in_rate + out_tok * out_rate) / 1_000_000

    def _maybe_log(
        self,
        template_name: str,
        model: str,
        prompt: str,
        parsed: BaseModel | None,
        outcome: str,
        provenance: Provenance | None = None,
    ) -> None:
        """Full-transcript logging is a TOGGLE (default off). Per-episode provenance is
        stored separately and always; this JSONL is the verbose prompt-debugging trail
        you want while tuning and can switch off in steady state."""
        if not self.settings.debug_logging:
            return
        self.settings.debug_log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "template": template_name,
            "model": model,
            "outcome": outcome,
            "prompt": prompt,
            "output": parsed.model_dump(mode="json") if parsed is not None else None,
            "provenance": provenance.model_dump(mode="json") if provenance is not None else None,
        }
        with self.settings.debug_log_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
