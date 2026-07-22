# Manuscript-to-Repository Alignment

Alignment target: Neurocomputing manuscript v35, dated 2026-07-22.

| Manuscript item | Repository evidence |
|---|---|
| Sec. 3.1, Eqs. 4-7 | `regularization.py`, `integrations/gr00t_n1_7/` |
| Sec. 3.2, rigid and hinge states | `scene.py`, `gaussian_ply.py`, hinge JSON schema |
| Sec. 3.3, Algorithm 1 | `pipeline.py`, `feasibility.py` |
| Table 1, platform and task settings | `configs/paper_reproduction.yaml` |
| Table 2, 3DGS quality | `table2_3dgs_scene_metrics.csv` |
| Table 3, hinge errors | `table3_structure_parameter_metrics.csv` |
| Figs. 6-8, iteration results | `iteration_results_long.csv`, `plot_iteration_results.py` |
| Table 4, intensity scan | `table4_feasibility_projection_alpha.csv` |
| Table 5, method comparison | `iteration_results_summary.csv`, final round |
| Table 6, ablation | `table6_ablation_statistics.csv` |
| Four-task deployment | `real_robot_trials.csv`, `table5_real_robot_trial_summary.csv` |

The vector files under `docs/assets/figures/` are copied from the v35
submission source. Website captions are outside the image files.

## Claims not made by the code

The release does not implement a new VLA network, does not add an inference
module, does not support prismatic structures, and does not validate force,
friction, or dynamic stability. Upstream simulators and reconstruction systems
are dependencies rather than contributions of this repository.
