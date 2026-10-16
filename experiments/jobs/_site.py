"""Site-specific SLURM and filesystem defaults based on $SYSTEMNAME.

Mirror of experiments/jobs/site_env.sh in Python. Used by the submit_*.py
launchers to auto-pick --account/--partition and the cluster virtualenv path.
CLI flags / override env vars continue to take precedence.

No site is configured in this release. Either set the override environment
variables (SLURM_ACCOUNT_OVERRIDE, SLURM_PARTITION_OVERRIDE, NASTJAPY_PATH)
or add your cluster to the two tables below, keyed by $SYSTEMNAME, e.g.

    SITE_TABLE = {"mycluster": ("my-account", "batch")}
    SITE_PATHS = {"mycluster": {"nastjapy": "/path/to/project/$USER/nastjapy",
                                "scratch":  "/path/to/scratch/$USER/async-abc"}}

and mirror the entry in site_env.sh.
"""
from __future__ import annotations

import os

SITE_TABLE: dict[str, tuple[str, str]] = {}

# Per-site filesystem defaults (mirror of the case statement in site_env.sh).
# "$USER" is expanded via os.path.expandvars at lookup time.
SITE_PATHS: dict[str, dict[str, str]] = {}


def detect_defaults() -> tuple[str, str]:
    """Return (account, partition) for the current $SYSTEMNAME.

    Honors SLURM_ACCOUNT_OVERRIDE / SLURM_PARTITION_OVERRIDE env vars.
    Raises RuntimeError on unknown $SYSTEMNAME unless both override env vars
    are set (in which case the overrides alone fully define the defaults).
    """
    override_account = os.environ.get("SLURM_ACCOUNT_OVERRIDE")
    override_partition = os.environ.get("SLURM_PARTITION_OVERRIDE")
    if override_account and override_partition:
        return override_account, override_partition

    sysname = os.environ.get("SYSTEMNAME", "")
    if sysname not in SITE_TABLE:
        raise RuntimeError(
            f"Unknown SYSTEMNAME={sysname!r}. "
            f"Pass --account/--partition explicitly, set SLURM_ACCOUNT_OVERRIDE / "
            f"SLURM_PARTITION_OVERRIDE, or extend experiments/jobs/_site.py."
        )
    account, partition = SITE_TABLE[sysname]
    account = override_account or account
    partition = override_partition or partition
    return account, partition


def detect_nastjapy_path() -> str:
    """Return the cluster virtualenv parent path for the current $SYSTEMNAME.

    Honors the NASTJAPY_PATH env var, which alone fully defines the path.
    Raises RuntimeError on unknown $SYSTEMNAME unless NASTJAPY_PATH is set.
    """
    override = os.environ.get("NASTJAPY_PATH")
    if override:
        return override

    sysname = os.environ.get("SYSTEMNAME", "")
    if sysname not in SITE_PATHS:
        raise RuntimeError(
            f"Unknown SYSTEMNAME={sysname!r}. "
            f"Pass --nastjapy-path explicitly, set NASTJAPY_PATH, or extend "
            f"experiments/jobs/_site.py."
        )
    return os.path.expandvars(SITE_PATHS[sysname]["nastjapy"])
