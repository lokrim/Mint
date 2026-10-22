# The Latent Guardian (Cerberus): Zhang, Li, Wu, Lee, Wang, ICML 2026 (PMLR v306)

- **Citation.** `zhang2026latentguardian`. PDF: https://raw.githubusercontent.com/mlresearch/v306/main/assets/zhang26cs/zhang26cs.pdf
- **Access.** FULL-SKIM on §3 (system and threat model), §4 (three consistency dimensions, adaptive threshold) and the latency table (Table 6). Read 2026-10-22.
- **Correction to findings 07.** arXiv 2506.22890 is **CP-uniGuard**, not Latent Guardian. The PMLR PDF is the correct source.

## Question, unit, inputs
- **Question.** Detect malicious collaborators by feature-level consistency instead of output consensus.
- **Unit.** One collaborator per frame (malicious or not).
- **Inputs.** Ego feature map vs each collaborator's feature map.

## Method
Three discrepancy scores against the ego:
1. **Topological integrity**: feature-level SSIM.
2. **Semantic direction**: cosine-type.
3. **Energy distribution shift**: activation magnitude.

The threshold is a mean + k·std rule ("99.7% of the normal distribution", i.e. 3σ), modulated by an uncertainty term from feature entropy that widens it under occlusion or bad weather. Evaluated on OPV2V and a second dataset (not extracted); latency per component reported (Table 6).

## Critique
- A 3σ rule assumes approximately Gaussian discrepancy scores. It is a heuristic threshold, not a calibrated probability.
- Widening thresholds under uncertainty trades sensitivity in exactly the regions attackers target (blind areas).
- Agent-level output.
- Comparisons quote LUCIA at about 10⁻² s latency.

## What transfers
- Three cheap feature-residual statistics as candidate evidence channels (`e_ssim`, `e_cos`, `e_energy`), computed **per tile** in the co-observed region only.

## Experiment
Include the three statistics in the M5 feature set. Run an ablation of their marginal value over the simpler L1 crop residual (AB-5).
