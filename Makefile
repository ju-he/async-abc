PYTHON ?= python
SCRIPTS := experiments/scripts
# Generators that draw from the committed data (the three vendoring scripts
# make_kfrontier_summary, make_ksweep_summary and make_twin_tables need the raw
# campaign output and are not listed).
FIGURE_SCRIPTS := $(filter-out $(SCRIPTS)/make_kfrontier_summary.py \
	$(SCRIPTS)/make_ksweep_summary.py $(SCRIPTS)/make_twin_tables.py, \
	$(wildcard $(SCRIPTS)/make_*.py))

.PHONY: figures schematic test example

figures:
	@set -e; for s in $(FIGURE_SCRIPTS); do echo "== $$s"; (cd $(SCRIPTS) && $(PYTHON) $$(basename $$s)); done

schematic:
	PYTHON=$(PYTHON) schematic/algorithm_strip/build.sh

test:
	$(PYTHON) -m pytest

example:
	$(PYTHON) examples/minimal.py
