# KPIS paper draft

`wtm_double.tex` is the main document. It continues the earlier seminar outline using the University of Hamburg WTM double-column template. The local `IEEEtran.cls` matches the class in `template_tex_paper_doublecol_wtm 2`. The source retains the template's A4 text area, conference layout, header conventions, and `plain` BibTeX style. `bib.bib` contains the references.

The two vector charts in `src/` are build inputs. The paper can be compiled directly from this directory or by uploading its source, bibliography, class, and `src/` to Overleaf and selecting `wtm_double.tex` as the main document.

```bash
cd paper
latexmk -pdf -outdir=build wtm_double.tex
```

With Tectonic, use `mkdir -p build && tectonic --outdir build wtm_double.tex`. The delivered PDF was built with latexmk, pdfLaTeX, and BibTeX (TeX Live 2026). Tectonic 0.17.0 also produced four pages. The delivered `wtm_double.pdf` includes references within the four-page limit.

## Regenerate the plots and summary

Run from the repository root with Python 3.10 or newer. The existing benchmark runner is needed only to collect new runs.

```bash
python3 -m venv /tmp/kpis-paper-venv
source /tmp/kpis-paper-venv/bin/activate
python3 -m pip install -r experiments/requirements-analysis.txt
python3 experiments/analyze_results.py \
  --input experiments/evidence/benchmark-results.csv \
  --output experiments/figures --expected-repetitions 3
cp experiments/figures/weighted_cost_comparison.pdf \
  experiments/figures/plan_length_comparison.pdf paper/src/
```

The [experiment provenance](../experiments/evidence/README.md) explains the saved benchmark settings and limitations. The generated `experiments/results/summary.csv` contains the values for Fig. 1 and Table I, including the timing and search effort columns.
