# Asynchronous, generation-free ABC

Code accompanying the paper *Asynchronous, Generation-Free ABC: Streaming AMIS
Reweighting for Heterogeneous Simulator Workloads on HPC*. It contains

- the asynchronous sampler, a propagator for the Propulate framework
  (`third_party/propulate/propulate/propagators/abcpmc.py`, class `ABCPMC`, with
  the history-based posterior estimator `extract_posterior`);
- the experiment library `async_abc` (`experiments/async_abc/`): benchmarks
  (Gaussian mean, g-and-k, Lotka–Volterra, Cellular Potts), the matched-kernel
  pyABC baseline, rejection ABC, runners, metrics, SBC, plotting;
- every experiment configuration (`experiments/configs/`), the runners
  (`experiments/scripts/*_runner.py`) and the SLURM launchers
  (`experiments/jobs/`);
- the summary data behind every figure and table
  (`experiments/data/paper_figures/`), the committed output of the diagnostics
  quoted in the text (`experiments/data/diagnostics/`), and the Cellular Potts
  reference data and two-parameter validation records
  (`experiments/data/cpm_*`);
- the scripts that regenerate each figure and table from that data, and the
  test suite.

## Installation

Python 3.10–3.12 (tested with 3.11 and 3.12). The asynchronous sampler needs the
**vendored** Propulate in `third_party/propulate`. Propulate from PyPI does not
contain it.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -c constraints.txt -e third_party/propulate -e ".[test,mpi]"
```

With uv: `uv venv && uv pip install -c constraints.txt -e third_party/propulate -e ".[test,mpi]"`.

`constraints.txt` pins the versions the test suite was run with. The paper's
runs used Python 3.12.3, NumPy 1.26.4, SciPy 1.13.1, mpi4py 4.0.1 and pyABC
0.12.17 under ParaStation MPI. `mpi4py` needs an MPI installation.

The Cellular Potts benchmark additionally needs the NAStJA simulator and its
Python wrapper `nastjapy` (package `nastja`). Everything else, including all
figures, works without them.

## Tests

```bash
pytest
```

This runs the experiment-library suite (`experiments/tests/`) and the
propagator's unit tests (`third_party/propulate/tests/test_abcpmc.py`).
In a fresh environment without nastjapy, 906 tests pass and 55 skip: 44
Cellular Potts tests need nastjapy, 8 tests launch `mpirun` themselves and skip
inside a pytest process that has already initialised MPI (they pass when
`experiments/tests/test_mpi_hardening.py` runs on its own), and 3 need a real
multi-rank MPI run.

## Regenerating the figures and tables

Every figure script reads the committed CSVs under
`experiments/data/paper_figures/<figure>/` and writes `figures/<figure>.pdf`.
No cluster access or raw data is needed:

```bash
make figures            # all data figures and table printouts
make schematic          # Fig. 1 (needs LaTeX with latexmk, TikZ, newtx)
```

or run a single script, e.g. `python experiments/scripts/make_barrier_fig.py`.

| Paper | Script (`experiments/scripts/`) | Data (`experiments/data/paper_figures/`) |
|---|---|---|
| Fig. 1, algorithm strip | `schematic/algorithm_strip/build.sh` | none (toy miniature run in `py/_toy2d.py`) |
| Fig. barrier | `make_barrier_fig.py` | `fig_predictor/` |
| Fig. scaling, Table scaling | `make_scaling_combined_fig.py` | `fig_scaling_combined/` |
| Fig. crossover, Table matched-ε | `make_crossover_fig.py`, `make_matched_eps_table.py` | `fig_crossover/`, `tab_matched_eps/` |
| Fig. SBC, Table SBC | `make_sbc_fig.py` | `fig_sbc_coverage/`, `fig_sbc_rank/` |
| Fig. reported recovery | `make_reported_recovery_fig.py` | `fig_reported_recovery/` |
| Fig. CPM posterior | `make_cpm_corner_fig.py` | `fig_cpm_corner/` |
| Table CPM production | `make_cpm_production_table.py` | `tab_cpm_production/` |
| Fig. heterogeneity quality | `make_hetero_fig.py` | `fig_hetero_quality/`, `fig_hetero_idle/` |
| Fig. barrier vs. pyABC | `make_barrier_pyabc_fig.py` | `fig_straggler_throughput/`, `fig_hetero_idle/` |
| Fig. ε curves | `make_eps_curves_fig.py` | `fig_eps_curves/` |
| Fig. parameter bias | `make_param_bias_fig.py` | `fig_param_bias/` |
| Fig. LV timing | `make_lv_timing_fig.py` | `fig_lv_timing/` |
| Fig. CPM utilisation | `make_cpm_util_fig.py` | `fig_cpm_util/` |
| Tables twin, twin-heterogeneity | `make_twin_rereport.py` | `tab_twin/`, `tab_twin_hetero/` |
| Table twin-CPM | `make_twin_cpm_decomposition.py` | `tab_twin_cpm/` |
| Table k-frontier | data only | `kfrontier_summary.csv` |
| Table (d, k, S) sweep | data only | `ksweep_summary.csv` |

Further scripts draw figures that are not in the paper (ablation, sensitivity,
predictor, Gaussian and posterior recovery, CPM difference and ε panels,
straggler throughput) or print the numbers quoted in the text.

**Data provenance.** The committed CSVs are small aggregates of the raw
per-particle records (about 30 GB for the Gaussian-mean experiment alone), which
are not part of this repository. Each generator can re-derive its CSVs from a
campaign output directory with `--refresh <campaign-root>`; the scripts that
only vendor data (`make_kfrontier_summary.py`, `make_ksweep_summary.py`,
`make_twin_tables.py`) need the campaign output and read its location from
`ASYNC_ABC_SCRATCH` (or `--scratch`). The `diag_*.py` scripts produced the
files in `experiments/data/diagnostics/`.

## Running the experiments

All runners share `--config`, `--output-dir`, `--test` (cheap smoke mode),
`--small` (reduced configs in `experiments/configs/small/`) and `--extend`
(resume). A local smoke test of the whole pipeline:

```bash
python experiments/run_all_paper_experiments.py --output-dir results/smoke --test
```

One benchmark under MPI, at the paper's worker count:

```bash
mpirun -n 48 python experiments/scripts/gaussian_mean_runner.py \
  --config experiments/configs/gaussian_mean.json --output-dir results/gaussian_mean
```

Main configurations: `gaussian_mean.json`, `gandk.json`, `lotka_volterra.json`,
`cellular_potts_two_param.json` / `_80.json` (benchmark comparisons),
`sbc*.json` (calibration), `straggler.json`, `runtime_heterogeneity.json`,
`hetero_twin*.json` (barrierized twin), `scaling.json` (strong scaling),
`sensitivity.json`, `ablation.json`. The paper's appendix lists which
configuration produced which result.

Each run writes `<output-dir>/<experiment>/{data,plots,logs}/`, with
`data/raw_results.csv` (one record per evaluated particle), `data/timing.csv`
and `data/metadata.json` (configuration, package versions, platform).

### On a SLURM cluster

The launchers in `experiments/jobs/` take the account, partition, scratch and
nastjapy locations from the environment:

```bash
export SLURM_ACCOUNT_OVERRIDE=<account> SLURM_PARTITION_OVERRIDE=<partition>
export SCRATCH_ROOT=/path/to/scratch NASTJAPY_PATH=/path/to/nastjapy
experiments/jobs/submit.sh experiments/jobs/run_experiments.sh $SCRATCH_ROOT/run1
python experiments/jobs/submit_scaling.py $SCRATCH_ROOT/scaling --dry-run
python experiments/jobs/submit_replicate_shards.py $SCRATCH_ROOT/run1 \
  --experiments gaussian_mean gandk --jobs-per-experiment 4 --dry-run
```

To make these defaults permanent for a cluster, add it to
`experiments/jobs/site_env.sh` and `_site.py`.

## Using the sampler on your own model

`examples/minimal.py` runs the sampler serially on a toy model in a few
seconds:

```python
prop = ABCPMC({"theta": (0.0, 1.0)}, k=100, kernel="gaussian", rng=random.Random(0))
history = []
for i in range(5000):
    cand = prop(history)                      # one candidate from the history so far
    cand.generation = i
    cand.loss = discrepancy(simulate(cand.position), y_obs)
    history.append(cand)
positions, weights = prop.extract_posterior(history)
```

In a parallel run Propulate makes these calls on every worker as results
arrive. `experiments/async_abc/inference/propulate_abc.py` shows the complete
MPI wiring used in the paper, including checkpointing, wall-clock budgets and
the posterior reconstruction.

## Licence

BSD 3-Clause (`LICENSE`). `third_party/propulate` keeps its own BSD 3-Clause
licence; its changes are listed in `third_party/propulate/MODIFICATIONS.md`.
