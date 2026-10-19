#!/usr/bin/env python3
"""Cellular Potts posterior corner, two-parameter setup (fig_cpm_corner.pdf).

Joint and marginal posteriors of ``division_rate`` and ``cell_volume`` on the
fixed production run (``tol_init`` 0.1, replicate 0, 3600 s on 48 workers) for
the three methods, each drawn from the object it reports:

* asynchronous -- the retroactive AMIS estimator (``posterior_weight`` over the
  full 12,835-evaluation history, every particle of positive weight);
* synchronous baseline -- its last generation completed inside the wall clock,
  with pyABC's importance weights (``pyabc_populations.csv.gz``);
* rejection ABC -- the 100 best of 13,000 prior draws on 48 ranks, the fairly
  resourced baseline (``best_k`` at the same evaluation budget as one
  asynchronous replicate).

Axes are the prior-normalised coordinates the inference runs in (log-uniform on
the physical ranges), ticked in physical units; dashed lines mark the truth
(0.009, 500). The joint panel outlines each method's 90 % highest-density region.
Densities are weighted Gaussian KDEs of the particles themselves, not of a
resample: resampling the 100-particle pyABC generation (ESS 38) only duplicates
particles, and SciPy's weighted KDE sets each bandwidth from the effective sample
size, so every method is smoothed according to the information it carries. The
vendored ``corner_samples.csv`` holds exactly the plotted particles and weights.
"""
from __future__ import annotations

import argparse
import io
import json
import tarfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy.stats import gaussian_kde

import _figdata as fd
from async_abc.plotting import paper_style as ps

NAME = "fig_cpm_corner"
DATA = Path(__file__).resolve().parents[1] / "data" / "cpm_two_param_validation"
ORDER = ["async", "sync", "rejection"]
_LS_NAME = {"-": "solid", "--": "dashed", ":": "dotted", "-.": "dashdot"}
X, Y = "division_rate", "cell_volume"
PHYS = {X: (0.001, 0.2), Y: (200.0, 1200.0)}
TRUTH_PHYS = {X: 0.009, Y: 500.0}
TICKS_PHYS = {X: [0.006, 0.009, 0.012], Y: [400, 500, 600, 800]}
# The posteriors occupy a small part of the prior box; show that part.
VIEW = {X: (0.29, 0.50), Y: (0.30, 0.80)}
# Posterior mass enclosed by the highest-density region drawn in the joint panel.
HDR_MASS = 0.9
K_REJECTION = 100
REPLICATE = 0
GRID = np.linspace(0.0, 1.0, 256)
_G2 = np.linspace(0.0, 1.0, 120)


def unit(name: str, x: float) -> float:
    lo, hi = PHYS[name]
    return float(np.log(x / lo) / np.log(hi / lo))


def aggregate(root: Path):
    df = pd.read_csv(root / "cpm_two_param_fixed/cellular_potts_two_param/data/raw_results.csv.gz")
    a = df[(df["method"] == "async_propulate_abc") & (df["replicate"] == REPLICATE)
           & (df["record_kind"] == "simulation_attempt")]
    w = a["posterior_weight"].to_numpy(float)
    ok = np.isfinite(w) & (w > 0)
    a, w = a[ok], w[ok] / w[ok].sum()
    frames = [pd.DataFrame({"method": "async", X: a[f"param_{X}"].to_numpy(), Y: a[f"param_{Y}"].to_numpy(),
                            "weight": w})]

    pops = pd.read_csv(root / "pyabc_populations.csv.gz")
    last = int(df[(df["method"] == "abc_smc_baseline") & (df["replicate"] == REPLICATE)
                  & (df["record_kind"] == "population_particle")]["generation"].max())
    s = pops[(pops["run"] == "50_fixed") & (pops["replicate"] == REPLICATE) & (pops["generation"] == last)]
    ws = s["weight"].to_numpy(float)
    frames.append(pd.DataFrame({"method": "sync", X: s[X].to_numpy(), Y: s[Y].to_numpy(), "weight": ws / ws.sum()}))

    corpus = []
    with tarfile.open(root / "cpm_fair_rejection.tar.gz") as tf:
        for m in tf.getmembers():
            if m.name.endswith(".jsonl"):
                for line in io.TextIOWrapper(tf.extractfile(m)):
                    r = json.loads(line)
                    corpus.append(dict(loss=float(r["loss"]), **{k: float(v) for k, v in r["params"].items()}))
    best = pd.DataFrame(corpus).nsmallest(K_REJECTION, "loss")
    frames.append(pd.DataFrame({"method": "rejection", X: best[X].to_numpy(), Y: best[Y].to_numpy(),
                                "weight": 1.0 / K_REJECTION}))
    out = pd.concat(frames, ignore_index=True)
    out["method"] = pd.Categorical(out["method"], categories=ORDER, ordered=True)
    return {"corner_samples": out}


def _ess(w) -> float:
    w = np.asarray(w, float)
    return float(w.sum() ** 2 / np.sum(w ** 2))


def _kde1(x, w):
    x = np.asarray(x, float)
    if len(x) < 2 or np.ptp(x) < 1e-9:
        return None
    try:
        return gaussian_kde(x, weights=w)(GRID)
    except np.linalg.LinAlgError:
        return None


def _kde2(x, y, w):
    x, y, w = np.asarray(x, float), np.asarray(y, float), np.asarray(w, float)
    if len(x) < 5 or np.ptp(x) < 1e-9 or np.ptp(y) < 1e-9:
        return None
    try:
        kde = gaussian_kde(np.vstack([x, y]), weights=w)
    except np.linalg.LinAlgError:
        return None
    xx, yy = np.meshgrid(_G2, _G2)
    z = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
    # Density level enclosing a given posterior mass: the weighted lower
    # quantile of the density evaluated at the particles themselves.
    at = kde(np.vstack([x, y]))
    order = np.argsort(at)
    cum = np.cumsum(w[order]) / w.sum()
    return xx, yy, z, float(at[order][np.searchsorted(cum, 1.0 - HDR_MASS)])


def _phys_ticks(ax, name: str, axis: str) -> None:
    pos = [unit(name, v) for v in TICKS_PHYS[name]]
    labels = [f"{v:g}" for v in TICKS_PHYS[name]]
    (ax.set_xticks if axis == "x" else ax.set_yticks)(pos)
    (ax.set_xticklabels if axis == "x" else ax.set_yticklabels)(labels)


def draw(frames):
    df = frames["corner_samples"]
    ess = {m: _ess(df.loc[df["method"] == m, "weight"]) for m in ORDER}
    fig, axes = plt.subplots(2, 2, figsize=ps.fig_size(0.62, aspect=0.9),
                             gridspec_kw={"wspace": 0.08, "hspace": 0.08})
    ax_x, ax_leg = axes[0]
    ax_j, ax_y = axes[1]
    for m in ORDER:
        sub = df[df["method"] == m]
        color, ls = ps.COLORS[m], ps.LINESTYLES[m]
        yk = _kde1(sub[X], sub["weight"])
        if yk is not None:
            ax_x.plot(GRID, yk, color=color, ls=ls, lw=1.3)
            ax_x.fill_between(GRID, yk, color=color, alpha=0.10, linewidth=0)
        yk = _kde1(sub[Y], sub["weight"])
        if yk is not None:
            ax_y.plot(GRID, yk, color=color, ls=ls, lw=1.3)
            ax_y.fill_between(GRID, yk, color=color, alpha=0.10, linewidth=0)
        kde2 = _kde2(sub[X], sub[Y], sub["weight"])
        if kde2 is not None:
            xx, yy, z, level = kde2
            ax_j.contourf(xx, yy, z, levels=[level, np.inf], colors=[color], alpha=0.10, zorder=2)
            ax_j.contour(xx, yy, z, levels=[level], colors=color, linestyles=_LS_NAME[ls],
                         linewidths=1.3, zorder=4)
    ref_kw = dict(color=ps.COLORS["reference"], ls=(0, (5, 3)), lw=0.8, alpha=0.7, zorder=1)
    tx, ty = unit(X, TRUTH_PHYS[X]), unit(Y, TRUTH_PHYS[Y])
    ax_x.axvline(tx, **ref_kw)
    ax_y.axvline(ty, **ref_kw)
    ax_j.axvline(tx, **ref_kw)
    ax_j.axhline(ty, **ref_kw)
    for ax in (ax_x, ax_j):
        ax.set_xlim(*VIEW[X])
    ax_y.set_xlim(*VIEW[Y])
    ax_j.set_ylim(*VIEW[Y])
    for ax in (ax_x, ax_j, ax_y):
        ax.grid(True, ls=":", lw=0.4, alpha=0.5)
    _phys_ticks(ax_j, X, "x")
    _phys_ticks(ax_j, Y, "y")
    _phys_ticks(ax_x, X, "x")
    _phys_ticks(ax_y, Y, "x")
    ax_x.set_xticklabels([])
    ax_x.set_yticks([])
    ax_y.set_yticks([])
    ax_j.set_xlabel("division rate")
    ax_j.set_ylabel("cell volume")
    ax_y.set_xlabel("cell volume")
    ax_leg.axis("off")
    handles = [Line2D([0], [0], color=ps.COLORS[m], ls=ps.LINESTYLES[m], lw=1.3,
                      label=f"{ps.LABELS[m]}\n(ESS {ess[m]:.0f})") for m in ORDER]
    handles.append(Line2D([0], [0], **{**ref_kw, "alpha": 1.0}, label="truth"))
    ax_leg.legend(handles=handles, loc="center", frameon=False, borderaxespad=0.0, handlelength=1.8, labelspacing=1.0)
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", nargs="?", const=str(DATA), default=None, metavar="DATA_ROOT")
    args = parser.parse_args()
    ps.apply()
    if args.refresh is not None:
        frames = aggregate(Path(args.refresh))
        vendor = frames
    else:
        frames = fd.load_vendored(NAME)
        vendor = None
    fig = draw(frames)
    saved = ps.save_paper_figure(fig, NAME, data=vendor)
    print(f"wrote {saved['pdf']}")


if __name__ == "__main__":
    main()
