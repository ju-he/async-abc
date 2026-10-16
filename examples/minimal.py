"""Minimal serial use of the asynchronous sampler on a one-parameter toy model.

Each call of the propagator returns one candidate built from the history so far;
in a parallel run Propulate makes these calls on every worker as results
arrive (see experiments/async_abc/inference/propulate_abc.py for the MPI
wiring used in the paper). The posterior is estimated afterwards from the full
history.
"""
import random
import numpy as np
from propulate.propagators import ABCPMC

rng = np.random.default_rng(0)
y_obs = 0.3                                   # observed summary statistic
limits = {"theta": (0.0, 1.0)}                # uniform prior box
prop = ABCPMC(limits, k=100, kernel="gaussian", rng=random.Random(0))

history = []
for i in range(5000):                         # one candidate per call
    cand = prop(history)
    cand.generation = i
    y_sim = rng.normal(cand.position[0], 0.05)
    cand.loss = abs(y_sim - y_obs)            # discrepancy
    history.append(cand)

positions, weights = prop.extract_posterior(history)
mean = np.average(positions[:, 0], weights=weights)
print(f"posterior mean {mean:.3f} from {len(history)} evaluations")
