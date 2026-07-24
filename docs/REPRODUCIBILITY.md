# Reproduction Guide

This guide separates lightweight validation from the GPU and simulator stages.

## 1. Validate the release

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,figures]"
python -m pytest
```

## 2. Validate local records and regenerate figures

Record-level experimental files are not included in the public repository.
With author-local or independently collected records, supply explicit paths:

```bash
python scripts/validate_paper_csvs.py \
  --data /path/to/private/result-records
python scripts/plot_iteration_results.py \
  --data /path/to/private/iteration-results.csv \
  --output-dir outputs/iteration_figures
```

The command creates separate vector plots for task success, accepted rollout
ratio, and action smoothness. It does not merge unlike metrics into one figure.

## 3. Prepare demonstrations

1. Synchronize external RGB, wrist RGB, robot state, action, timestamp, task,
   and episode identifiers at 30 Hz.
2. Convert each episode to the GR00T-compatible LeRobot v2 layout.
3. Freeze train, validation, and test episode identifiers before augmentation.
4. Compute normalization statistics from the training split only.

The release does not publish raw laboratory video. The required data fields and
split boundary are documented in the manuscript appendix.

## 4. Train the initial policy

Clone the tagged GR00T N1.7 upstream separately. Install this repository in the
same environment and apply the hook described in
`integrations/gr00t_n1_7/README.md`. Resolve all parameters from
`configs/paper_reproduction.yaml` and record each run:

```bash
python scripts/record_run_manifest.py \
  --checkpoint /path/to/checkpoint \
  --source-tree /path/to/training/source \
  --started-at 2026-01-01T00:00:00Z \
  --finished-at 2026-01-01T03:00:00Z \
  --training-command "<resolved command>" \
  --output outputs/run_manifest.json
```

## 5. Build object-decoupled scene assets

1. Calibrate multiview cameras and generate instance masks.
2. Train foreground-object and completed-background 3DGS assets.
3. Normalize each object in a local reference frame.
4. For hinged objects, annotate the axis, center, and lower and upper limits.
5. Split the Gaussian PLY while retaining all 3DGS fields.
6. Use pinned 3DGRUT to export visible assets and collision proxies.
7. Assemble rigid and revolute-joint assets in Isaac Sim and verify units.

The PLY splitter is provided in `scripts/split_gaussian_asset.py`; the hinge
metadata contract is `examples/structured_scene/hinge_metadata.schema.json`.

## 6. Run screened virtual rollouts

Implement simulator-specific adapters for `run_closed_loop_expansion`. Each
candidate must record its seed, active checkpoint, source episode, sampled
state, automatic-check values, manual-review decision, and rejection reason.
Only accepted episodes are passed to the incremental trainer.

The policy returns an action chunk of length \(H\). The rollout adapter executes
the first eight actions, acquires a new observation, and requests a new action
chunk. This receding-horizon rule is repeated until success, failure, or the
episode timeout.

The implemented predicate covers collision proxies, workspace, joint limits,
target visibility, hinge limits, structural residuals, and action smoothness.
It does not establish contact-force, friction, or dynamic-stability validity.

## 7. Evaluate without cross-batch mixing

Run the four-task deployment, three-task method comparison, intensity scan, and
four-task paired ablation as separate batches. Keep seeds, task membership,
denominators, and aggregation units explicit. Do not pool the 86.3%, 84.8%, and
84.4% results because they answer different questions.
