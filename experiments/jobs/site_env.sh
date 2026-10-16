#!/usr/bin/env bash
# Source this file (do not execute). Exports SITE_ACCOUNT, SITE_PARTITION,
# SITE_NASTJAPY_PATH and SITE_SCRATCH_ROOT. This is the single source of truth
# for per-cluster SLURM and filesystem defaults; the Python mirror lives in
# _site.py.
#
# Source it ON THE LOGIN NODE (e.g. from submit.sh) — a submitted #SBATCH
# script runs from SLURM's spool copy and cannot locate this file, so the
# launchers inject the resolved paths into the job environment via
# `sbatch --export` instead.
#
# No site is configured in this release: set SLURM_ACCOUNT_OVERRIDE,
# SLURM_PARTITION_OVERRIDE, NASTJAPY_PATH and SCRATCH_ROOT, or add a case for
# your $SYSTEMNAME below (and mirror it in _site.py). Fails loudly otherwise.

case "${SYSTEMNAME:-}" in
    # mycluster)
    #     SITE_ACCOUNT="my-account" ; SITE_PARTITION="batch"
    #     SITE_NASTJAPY_PATH="/path/to/project/$USER/nastjapy"
    #     SITE_SCRATCH_ROOT="/path/to/scratch/$USER/async-abc"
    #     ;;
    *)
        if [[ -z "${SLURM_ACCOUNT_OVERRIDE:-}" || -z "${SLURM_PARTITION_OVERRIDE:-}" \
              || -z "${NASTJAPY_PATH:-}" || -z "${SCRATCH_ROOT:-}" ]]; then
            echo "site_env.sh: unknown SYSTEMNAME='${SYSTEMNAME:-<unset>}'." >&2
            echo "  Set SLURM_ACCOUNT_OVERRIDE / SLURM_PARTITION_OVERRIDE / NASTJAPY_PATH / SCRATCH_ROOT, or extend site_env.sh." >&2
            return 1 2>/dev/null || exit 1
        fi
        ;;
esac

SITE_ACCOUNT="${SLURM_ACCOUNT_OVERRIDE:-$SITE_ACCOUNT}"
SITE_PARTITION="${SLURM_PARTITION_OVERRIDE:-$SITE_PARTITION}"
SITE_NASTJAPY_PATH="${NASTJAPY_PATH:-$SITE_NASTJAPY_PATH}"
SITE_SCRATCH_ROOT="${SCRATCH_ROOT:-$SITE_SCRATCH_ROOT}"
export SITE_ACCOUNT SITE_PARTITION SITE_NASTJAPY_PATH SITE_SCRATCH_ROOT
