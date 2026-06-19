# marginal-tigers

Automated, text-only content pipeline for the **Marginal Tigers** Instagram account
(Stefan & Jan, two plush tigers, deadpan economics punchlines).

**The operating spec lives in [`CLAUDE.md`](./CLAUDE.md)** — read it first; it encodes the
design decisions (two-tier storage, slot-mode generation, gate taxonomy, CLI surface).

> Names: import package `marginal_tigers`; CLI command `marginal`; repo `marginal-tigers`.

## Layout

```
marginal-tigers/
├── CLAUDE.md                       # standing context + operating rules
├── pyproject.toml                  # package metadata + `marginal` console script
├── src/marginal_tigers/            # package code
│   ├── __init__.py
│   ├── cli.py                      # CLI entry point (Typer app lands here; placeholder for now)
│   ├── schemas.py                  # Pydantic v2 data contracts
│   └── llm.py                      # LLMSettings + the single structured-output call
├── world/                          # Tier-1 source of truth (git, hand-edited)
│   ├── bible.yaml                  # characters, world, cast, antagonist, style
│   └── econ_concepts.yaml          # the finite econ-concept library
└── tests/
```

`data/` (Tier-2 SQLite) and `.env` are gitignored and never committed (see `CLAUDE.md` §15).

## Develop

Requires Python 3.12 (per `CLAUDE.md` §16).

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Status

Scaffold + Tier-1 content + core schemas/LLM config are in place. The Typer CLI verbs
(`plan-year`, `plan-week`, `generate`, `regenerate`, `review`, `backup`) and the generation
DAG are not yet implemented.
