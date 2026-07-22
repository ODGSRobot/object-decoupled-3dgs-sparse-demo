# GR00T N1.7 training integration

The manuscript uses the released GR00T N1.7 architecture and inference path.
The only policy-side change is the training objective. The action head retains
its original flow-matching loss and adds two masked sequence terms while
training:

```python
from regularization_hook import apply_training_regularization

loss, loss_log = apply_training_regularization(
    flow_matching_loss=flow_matching_loss,
    pred_velocity=pred_actions,
    noisy_trajectory=noisy_trajectory,
    time=t,
    action_mask=action_mask,
    temporal_weight=0.05,
    velocity_weight=0.02,
)
```

Insert the call after the original masked flow-matching loss is computed in the
N1.7 action head. Expose the following configuration fields through the model
and fine-tuning configuration:

```text
sparse_demo_algorithm_variant
sparse_demo_temporal_consistency_weight
sparse_demo_velocity_smoothness_weight
```

For `base`, set both weights to zero and use the original loss. For
`sparse_demo_temporal`, use the values resolved in
`configs/paper_reproduction.yaml`. The wrapper script accepts the path to a
separately cloned N1.7 tree:

```powershell
powershell -ExecutionPolicy Bypass -File integrations/gr00t_n1_7/launch_finetune_variant.ps1 `
  -GrootRoot C:\src\Isaac-GR00T `
  -Variant sparse_demo_temporal `
  -TemporalWeight 0.05 `
  -VelocityWeight 0.02 `
  --base-model-path nvidia/GR00T-N1.7-3B `
  --dataset-path C:\data\single_arm_lerobot `
  --embodiment-tag NEW_EMBODIMENT
```

No regularization module is called during policy inference. The network
architecture, action horizon, sampler, and action decoder remain unchanged.
