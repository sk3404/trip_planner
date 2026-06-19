# marginal-tigers

A small Python package, `marginal_tigers`, that installs a `marginal` command-line tool.

## Install

```bash
pip install -e .
```

## Usage

```bash
marginal --help
marginal hello
marginal hello Tigers
marginal --version
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Layout

```
marginal-tigers/
├── pyproject.toml          # package metadata + `marginal` console script
├── marginal_tigers/        # the importable package
│   ├── __init__.py
│   └── cli.py              # CLI entry point (marginal_tigers.cli:main)
└── tests/
    └── test_cli.py
```
