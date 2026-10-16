#!/usr/bin/env bash
# Fig. 1 (algorithm strip): draw the twelve panels from the toy miniature runs
# in py/_toy2d.py, then typeset the TikZ wrapper around them. Needs a LaTeX
# installation with latexmk, TikZ, standalone and newtx. Writes
# figures/fig_algorithm_strip.pdf at the repository root.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python}
mkdir -p out
$PY py/a8_algorithm_panels.py
$PY py/a9_pmc_panels.py
( cd tikz && latexmk -pdf -interaction=nonstopmode -halt-on-error -output-directory=../out a10_algorithm_strip.tex > ../out/a10_algorithm_strip.buildlog 2>&1 ) \
  || { echo "LaTeX failed, see out/a10_algorithm_strip.buildlog" >&2; exit 1; }
mkdir -p ../../figures
cp out/a10_algorithm_strip.pdf ../../figures/fig_algorithm_strip.pdf
echo "wrote figures/fig_algorithm_strip.pdf"
