# MINT viva study notes — start here

Written 2026-10-28 for the final B.Tech evaluation. Built only from this repository:
the final paper [`paper/main.tex`](../../paper/main.tex), its generated numbers [`paper/numbers.tex`](../../paper/numbers.tex) and tables [`paper/tables/`](../../paper/tables/), the reviewer Q&A [`planning/project_qa_for_reviewers.md`](../project_qa_for_reviewers.md), the test interpretation draft [`planning/final_report_interpretation_DRAFT.md`](../final_report_interpretation_DRAFT.md), the planning documents, and the code in [`src/mint/`](../../src/mint/).

## Read this first: one important correction to the study prompt

The study prompt talks about "the original research paper" and "what our student group did" as if MINT were someone else's paper that we studied. **The supplied materials say otherwise.**

- The MINT paper (`paper/main.tex`) lists **our group as its authors**: Ahmed Zyed K.A., Alan Saji, Farhaan Nizam, Sreyas S Warrier, with Shameem Ansar A and Chinnu Jacob, TKM College of Engineering, Kollam.
- The repository contains the code that implements MINT (`src/mint/`), the attacks, the baselines, the evaluation runners (`runners/`), and the logged runs (`runs/`), including the one-time final test (`runs/20261024-E5v3/`) and the Culver City run (`runs/20261026-CULVER/`).
- So in this project, **"the paper's authors" and "our group" are the same people.**

What we did **not** do (and must never claim):
- We did **not** train the detector. We used the **released AttFuse checkpoint** from the OpenCOOD framework, unchanged (paper §III-A, §V-E).
- We did **not** create the dataset. OPV2V was made by Xu et al. (2022) with the CARLA simulator.
- We did **not** test on real vehicles or real-sensor data. Everything is simulated.
- We did **not** compare against learned defenses such as LUCIA, MADE or CP-Guard in experiments. They appear only in the literature review.

One more honest point: the repository history is under a single git account, so it does not record which member did which part. **Each member should describe their own role truthfully in their own words.** Part 6 has a template.

There is no separate "project report" in the folder with an "Objectives" chapter. The closest things are: the paper (`paper/main.tex`), the automatically generated test report (`runs/20261024-E5v3/report/report.md`, which still uses the old method name **R1**), and the Culver City report (`runs/20261026-CULVER/report/report.md`). These notes follow the **paper's** section order. Where the prompt asks for a section the paper does not have (for example "Objectives"), the notes build it from the paper's research question and contributions, and say so.

## Names you will see

| Name | Meaning |
|---|---|
| **MINT** | **M**essage **IN**fluence **T**esting — the final name of our method (paper title). |
| **R1** | The old internal code name of the same method. Used in the test report, code (`src/mint/reliability/r1.py`) and planning files. **R1 = MINT.** The paper never uses "R1". |
| "Multi-agent Inbound Node Trust" | An early project name in planning documents (e.g. `planning/research_charter.md`). Abandoned. Do not use it. |
| Block T / Block H | Development-era names for the **design set** and **validation set**. The paper uses "design" and "validation". |
| E0…E5 | Development experiment numbers. Not used in the paper. |

## Files

| File | Contents | When to read |
|---|---|---|
| [01_big_picture_and_objectives.md](01_big_picture_and_objectives.md) | Part 1: ELI5, 30 s / 1 min / 3 min explanations, five objectives, glossary | Tonight, first |
| [02_report_sections.md](02_report_sections.md) | Part 2: abstract, introduction, problem and gap, related work, threat model, objectives — section by section | Tonight |
| [03_methodology.md](03_methodology.md) | Part 3: the method from zero — counterfactual, ADD/REMOVE/SHIFT, matching, tiles, LiDAR rays, KNOWN/UNKNOWN, Wilson interval, gating, full algorithm, baselines | Tonight, slowly — most important |
| [04_setup_and_results.md](04_setup_and_results.md) | Parts 4–5: what was built, data, attacks, fairness, metrics, every main number with source, the results story, AP definitions, discussion, limitations, conclusion | Tonight |
| [05_viva_and_revision.md](05_viva_and_revision.md) | Part 6: 60+ viva questions with answers, honest-contribution script, rapid revision sheets | Tomorrow morning |

## How to revise

1. Tonight: read 01 → 03 → 04 in order. Say the "viva answer" boxes out loud.
2. Tomorrow morning: only 05 (the revision sheets at the end take 15 minutes).
3. If you forget a number, it is better to say "about" and give the direction than to invent a precise value. Every number in these notes has its source next to it.

## Labels used in the notes

- **[SOURCE]** — stated in the paper or repository (location given).
- **[ANALOGY]** — an everyday comparison made up for teaching. Not part of the paper.
- **[TEACHING EXAMPLE]** — invented numbers for explanation. **Not an experimental result.**
- **[INTERPRETATION]** — my reading of the evidence; say "we interpret this as…" in the viva.
