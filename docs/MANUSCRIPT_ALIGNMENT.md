# Manuscript-to-Repository Alignment

Alignment target: Neurocomputing manuscript v37, dated 2026-07-24.

| Manuscript item | Repository evidence |
|---|---|
| Sec. 3.1, Eqs. 4-7 | `regularization.py`, `integrations/gr00t_n1_7/` |
| Sec. 3.2, rigid and hinge states | `scene.py`, `gaussian_ply.py`, hinge JSON schema |
| Sec. 3.3, Algorithm 1 | `pipeline.py`, `feasibility.py` |
| Table 1, platform and task settings | `configs/paper_reproduction.yaml` |
| Tables 2-6 and Figs. 6-8 | Metric, plotting, and validation implementations; record-level inputs remain private |
| Four-task deployment | Evaluation protocol in the manuscript; record-level inputs remain private |

The vector files under `docs/assets/figures/` are synchronized with the v37
submission source. Website captions are outside the image files.

## Scene-symbol mapping

The manuscript separates static asset data from a sampled scene state:

- \(\mathcal{A}\) denotes static object assets, including object-local Gaussian
  support, local frames, rigid or hinge parameters, and collision proxies.
  These fields map to `HingeModel`, Gaussian PLY metadata, and asset files.
- \(\mathcal{Z}\) denotes the current randomized robot, object, target, and hinge
  state. It maps to `SampledSceneState`.
- \(\mathcal{S}=(\mathcal{G},\mathcal{A},\mathcal{Z})\) denotes one instantiated
  scene used by the rollout adapter. The static assets remain unchanged while
  `sample_scene_state` updates \(\mathcal{Z}\).

## Claims not made by the code

The release does not implement a new VLA network, does not add an inference
module, does not support prismatic structures, and does not validate force,
friction, or dynamic stability. Upstream simulators and reconstruction systems
are dependencies rather than contributions of this repository.
