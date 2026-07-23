# Paper-Facing Data Records

`examples/real_data/` is synchronized with the current manuscript evidence
tables. The filenames describe the statistical content rather than obsolete
figure numbers.

| File | Role | Rows |
|---|---|---:|
| `iteration_results_long.csv` | Per-task, per-method, per-round, per-seed rollout and policy records | 420 |
| `iteration_results_summary.csv` | Count-preserving summaries for iteration plots | 112 |
| `rollout_rejection_diagnostics.csv` | Non-exclusive rejection-trigger frequencies | 63 |
| `real_robot_trials.csv` | Four-task deployment trial labels, excluding drawer opening | 210 |
| `table2_3dgs_scene_metrics.csv` | Nine-scene held-out-view PSNR, SSIM, and LPIPS | 9 |
| `table3_structure_parameter_metrics.csv` | Medicine-box and microwave hinge errors | 2 |
| `table4_feasibility_projection_alpha.csv` | Perturbation-intensity scan | 7 |
| `table5_real_robot_trial_summary.csv` | Four-task deployment summary and total | 5 |
| `table6_ablation_statistics.csv` | Four-task paired task-by-seed ablation | 6 |

## Denominators

For each rollout record:

```text
accepted + rejected = candidates
acceptance = accepted / candidates
total rejection = rejected / candidates = 1 - acceptance
```

Collision, workspace, articulation, visibility, and smoothness diagnostic flags
can co-occur. Their rates identify triggered checks and must not be summed to
obtain total rejection.

The paper uses four nonoverlapping evaluation batches:

| Batch | Task set | Aggregation |
|---|---|---|
| Real deployment | 4 tasks, 210 trials | Trial weighted |
| Method comparison | 3 tasks, 300 trials per method | Trial weighted |
| Intensity scan | Fixed candidate and trial budgets at each intensity | Count and seed summaries |
| Ablation | 4 tasks x 5 seeds = 20 cells | Unweighted paired macro mean |

Drawer opening is excluded from the current real deployment and ablation scope.

## Execution-quality fields

`execution_steps` is the number of 30 Hz control steps from the start of a
complete episode to termination. It is an episode-duration measure in control
steps, not accumulated joint-space or end-effector distance.

`action_smoothness` is the temporal mean of the squared Euclidean norm of the
second-order executed-action difference:

```text
mean_t ||a[t+2] - 2 a[t+1] + a[t]||_2^2
```

The value is computed from the executed action sequence. Lower values indicate
smaller discrete action curvature and smoother control.

## Validation

```bash
python scripts/validate_paper_csvs.py --data examples/real_data
```

The validator checks required fields, count-rate identities, nonempty tables,
and the drawer-task exclusion. It does not infer or repair experimental values.

## Large Assets

Raw camera video, Gaussian point clouds, USDZ assets, and checkpoints are not
stored in this Git repository. Access to laboratory video and licensed hardware
assets is evaluated under the applicable privacy and third-party license
conditions.
