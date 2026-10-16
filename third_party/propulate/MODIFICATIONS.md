# Vendored Propulate

This directory is a snapshot of Propulate 1.2.2 (upstream:
https://github.com/Helmholtz-AI-Energy/propulate, BSD 3-Clause, see
`LICENSE.md`) with the changes this work needs:

- `propulate/propagators/abcpmc.py`: the asynchronous ABC propagator (class
  `ABCPMC`), its tolerance schedulers and the history-based posterior
  estimator `extract_posterior`;
- `propulate/propulator.py`, `population.py`, `pollinator.py`, `migrator.py`,
  `propagators/base.py`: support for it (worker context passed to
  propagators, tolerance and weight fields on individuals, an incrementally
  maintained active-population view, categorical/ordinal parameter handling,
  checkpoint recovery from the backup file, lazy GPy import);
- `pyproject.toml`: dependencies reduced to what this package imports.

`tests/test_abcpmc.py` is the propagator's unit-test suite; it runs as part of
the repository's `pytest`.
