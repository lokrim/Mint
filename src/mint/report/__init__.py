"""Reporting pipeline for the E5 final test: figures, tables and a markdown report built ONLY from the two
analysis summaries (e5_test.json from the frozen v2 analysis, e5_v3.json from v3_analyze). It never reads the
per-frame caches (cache/, v3extra/) and never recomputes a statistic; every number shown is copied from those
files. Dependencies: numpy, matplotlib, jinja2 (no torch, no OpenCOOD).
"""
