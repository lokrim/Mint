# Citation verification, 2026-10-27

Scope: every `[CITATION NEEDED]` in `paper/main.tex` (as listed in `paper/README.md`, "TODO left in the draft"), the two uncited items (Wilson 1927, the bootstrap), and every `paper/refs.bib` entry. Each row was checked against a primary or authoritative bibliographic source: the publisher page metadata (USENIX, PMLR, NeurIPS, CVF open access), the Crossref record behind the DOI, or the arXiv API record. Bibliographic fields only; content access levels are unchanged and stay in the bib `note`/`mintaccess` field.

Status: **verified** = fields in the bib matched the source; **corrected** = a field was wrong or missing and was fixed or added; **preprint** = arXiv only, no journal-ref or DOI on arXiv as of 2026-10-27; **unverifiable** = none this round.

Machine lookups (arXiv API, Crossref, OpenAlex, publisher pages) are not counted as web searches. Web searches used: 10 of the ~25 budget (3 for citations, 7 for novelty; see [search_log.md](search_log.md) Q15–Q24).

## Former `[CITATION NEEDED]` markers (now `\cite`)

| Key | Verified fields | Source | Status |
|---|---|---|---|
| `tao2026mvig` (MVIG) | Tao, Hu, An, Fang (Zhengru), Cao, Fang (Yuguang); "Learning Mutual View Information Graph for Adaptive Adversarial Collaborative Perception"; CVPR 2026, pp. 42321–42330; arXiv 2602.19596 | https://openaccess.thecvf.com/content/CVPR2026/html/Tao_Learning_Mutual_View_Information_Graph_for_Adaptive_Adversarial_Collaborative_Perception_CVPR_2026_paper.html | verified (new entry). **Published at CVPR 2026, not a preprint.** The audit's "preprint" label is outdated. |
| `everingham2010voc` (PASCAL VOC AP) | Everingham, Van Gool, Williams, Winn, Zisserman; IJCV 88(2):303–338, 2010; DOI 10.1007/s11263-009-0275-4 | https://doi.org/10.1007/s11263-009-0275-4 (Crossref) | verified (new). Online 2009, issue 2010. |
| `nosek2018preregistration` (pre-registration practice) | Nosek, Ebersole, DeHaven, Mellor; "The Preregistration Revolution"; PNAS 115(11):2600–2606, 2018; DOI 10.1073/pnas.1708274114 | https://doi.org/10.1073/pnas.1708274114 (Crossref) | verified (new). Supports "pre-registration" as a practice. It does not support the claim that it is rare in CP; that claim stays our own. |
| `holm1979` | Holm, S.; "A Simple Sequentially Rejective Multiple Test Procedure"; Scand. J. Statist. 6(2):65–70, 1979; DOI 10.2307/4615733 | https://api.openalex.org/works/W2121044470 (DOI 10.2307/4615733); JSTOR https://www.jstor.org/stable/4615733 | verified (new). The JSTOR page cannot be read by a script (JS challenge), and Crossref has no record for this DOI. Volume, pages, year and DOI come from OpenAlex. Issue 2 comes from GESIS and JSTOR-copy metadata seen in search results. |
| `dosovitskiy2017carla` (CARLA) | Dosovitskiy, Ros, Codevilla, Lopez, Koltun; CoRL 2017, PMLR 78:1–16 | https://proceedings.mlr.press/v78/dosovitskiy17a.html | verified (new) |

## Previously uncited, now cited at first use

| Key | Verified fields | Source | Status |
|---|---|---|---|
| `wilson1927` | Wilson, E. B.; "Probable Inference, the Law of Succession, and Statistical Inference"; JASA 22(158):209–212, 1927 | https://doi.org/10.1080/01621459.1927.10502953 (Crossref) | verified (new); cited at the Wilson interval (§ Resolvability gate) |
| `efron1979bootstrap` | Efron, B.; "Bootstrap Methods: Another Look at the Jackknife"; Ann. Statist. 7(1):1–26, 1979 | https://doi.org/10.1214/aos/1176344552 (Crossref) | verified (new); cited at the scenario bootstrap (§ Statistics). The cluster and block variants are not attributed to a specific paper. |

## Existing `refs.bib` entries

| Key | Verified fields | Source | Status |
|---|---|---|---|
| `xu2022opv2v` | authors, title, ICRA 2022, pp. 2583–2589 | https://doi.org/10.1109/ICRA46639.2022.9812038 | verified (+DOI) |
| `lang2019pointpillars` | authors, title, CVPR 2019 | https://doi.org/10.1109/CVPR.2019.01298 | **corrected**: pages 12697–12705 → 12689–12697 (IEEE Xplore). The CVF open-access copy uses the old numbering. +DOI |
| `tu2021adversarial` | authors, title, ICCV 2021 | https://doi.org/10.1109/ICCV48922.2021.00767 | corrected (pages 7748–7757 and DOI added) |
| `zhang2024cad` | 7 authors, title, USENIX Security 2024 | https://www.usenix.org/conference/usenixsecurity24/presentation/zhang-qingzhao | corrected (pages 6309–6326 added) |
| `sun2020carlo` | authors, title, USENIX Security 2020, pp. 877–894 | https://www.usenix.org/conference/usenixsecurity20/presentation/sun | verified (the "verify" flag on the page range is now cleared) |
| `hau2021shadowcatcher` | authors, title, ESORICS 2021 (LNCS), DOI | https://doi.org/10.1007/978-3-030-88418-5_33 | corrected (pages 691–711 added) |
| `zhao2024made` | authors (Wang before Chen, as published; the arXiv order differs), title, IROS 2024 | https://doi.org/10.1109/IROS58592.2024.10801337 | verified (venue confirmed; pages 13817–13823 and DOI added) |
| `li2023robosac` | authors, title, ICCV 2023 | https://doi.org/10.1109/ICCV51070.2023.00024 | corrected (pages 186–195 and DOI added) |
| `hu2025cpguard` | 7 authors, title, AAAI-25 | https://doi.org/10.1609/aaai.v39i22.34486 | corrected (vol. 39, no. 22, pp. 23203–23211 and DOI added) |
| `wang2025lucia` | 9 authors, title, USENIX Security 2025, pp. 7387–7406 | https://www.usenix.org/conference/usenixsecurity25/presentation/wang-chenyi | verified |
| `hallyburton2025mate` | authors, title, CCS 2025, pp. 2009–2023, DOI | https://doi.org/10.1145/3719027.3765193 | verified ("verify" flag cleared) |
| `tao2026gcp` | 6 authors, title, IEEE TDSC 2026 | https://doi.org/10.1109/TDSC.2026.3693684 | verified (venue confirmed; vol. 23, no. 4, pp. 9535–9548 and DOI added) |
| `zhang2026latentguardian` | 5 authors, title, ICML 2026, PMLR 306 | https://proceedings.mlr.press/v306/zhang26cs.html | corrected (pages 156696–156712 added) |
| `liu2026trustflip` | 4 authors, title, arXiv 2605.22122 v2 (28 Aug 2026) | https://arxiv.org/abs/2605.22122 | preprint |
| `zhang2026poseguard` | 3 authors, title, arXiv 2605.01301 v2 (11 Sep 2026) | https://arxiv.org/abs/2605.01301 | preprint |
| `cao2019advlidar` | 9 authors, title, CCS 2019 | https://doi.org/10.1145/3319535.3339815 | corrected (pages 2267–2281 and DOI added) |
| `madry2018pgd` | 5 authors, title, ICLR 2018 | https://iclr.cc/virtual/2018/poster/67; OpenReview rJzIBfZAb (page blocked to scripts; ID from MIT DSpace record); arXiv 1706.06083 | verified (+eprint) |
| `carlini2019evaluating` | 9 authors, title, arXiv 1902.06705 | https://arxiv.org/abs/1902.06705 | preprint (a living document; never peer-reviewed) |
| `tramer2020adaptive` | 4 authors, title, NeurIPS 2020 | https://proceedings.neurips.cc/paper/2020/hash/11f38f8ecd71867b42433548d1078e38-Abstract.html | corrected (vol. 33, pp. 1633–1645 added) |
| `xu2023v2v4real` | 13 authors, title, CVPR 2023, pp. 13712–13722 | https://doi.org/10.1109/CVPR52729.2023.01318 | verified (+DOI) |
| `xu2022v2xvit` | 6 authors, title, ECCV 2022, pp. 107–124 | https://doi.org/10.1007/978-3-031-19842-7_7 | verified (+DOI) |
| `hu2022where2comm` | 5 authors, title, NeurIPS 35, pp. 4874–4886 | https://proceedings.neurips.cc/paper_files/paper/2022/hash/1f5c5cd01b864d53cc5fa0a3472e152e-Abstract-Conference.html | verified |
| `he2026glst` | 6 authors, title, arXiv 2607.23059 v1 (25 Jul 2026) | https://arxiv.org/abs/2607.23059 | preprint |
| `luo2025mixedsignals` | 12 authors, title, ICCV 2025 | https://doi.org/10.1109/ICCV51701.2025.02671 | corrected (pages 28763–28773 and DOI added) |
| `benjamini1995fdr` | authors, title, JRSS-B 57(1):289–300, 1995 | https://doi.org/10.1111/j.2517-6161.1995.tb02031.x | verified (+DOI) |

The arXiv metadata for all preprints and arXiv-backed entries was pulled from `export.arxiv.org/api/query` on 2026-10-27.

## Also changed in `planning/literature/references.bib` only (not cited in the paper)

- `yu2026prbi` (PRBI): was `@misc`, now `@inproceedings`. Published at CVPR 2026, pp. 6549–6558 (CVF open-access page).
- Two new screened preprints from the novelty search: `liu2026saber` (2610.07875) and `wang2026hetshield` (2609.17856).
- Not re-checked: `hu2026cpuniguard`. A search listing shows it in IEEE TMC 2026 (vol. 25, no. 6), but we saw only a snippet, so its entry is left as an arXiv preprint.

## Unverifiable

None. No citation was invented, and no `[CITATION NEEDED]` remains in `main.tex`. The `\CITENEEDED` macro definition is kept for future use.

## Not done here (outside the allowed files)

- The "TODO left in the draft" list in `paper/README.md` still names these citations as open. It should be trimmed in a commit that is allowed to touch the README.
- The Overleaf zip has not been rebuilt.
- The paper was not compiled: there is no TeX installation on this machine. A static check confirms that all 32 `\cite` keys resolve in `refs.bib`, that there are no duplicate keys, and that braces balance.
