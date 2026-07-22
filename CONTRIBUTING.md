# Contributing

Issues and pull requests should remain within the paper's technical scope:
training-only sequence regularization, object/background-decoupled 3DGS assets,
rigid or hinged structure metadata, rollout screening, provenance, evaluation,
and reproduction tooling.

Before opening a pull request:

```bash
python -m pip install -e ".[dev,figures]"
python scripts/validate_paper_csvs.py
python -m pytest
ruff check src scripts tests integrations
```

Do not commit raw participant or laboratory video, credentials, checkpoints,
licensed upstream code, manuscripts, EndNote libraries, or generated revision
artifacts. New result values must include a documented source and aggregation
rule. A pull request must not replace measured results with synthetic values.
