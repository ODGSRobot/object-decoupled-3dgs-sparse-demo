# Public Release Checklist

This checklist records the intended boundary of the paper repository. It is a
release-control document, not an experimental claim.

## Included

- Reference implementations for the training-only regularizers, rigid and
  hinge scene states, Gaussian PLY splitting, rollout screening, and the
  incremental update loop.
- Resolved paper configuration and pinned upstream versions.
- Unit tests and optional private-data schema validation utilities.
- Separate vector result plots and the source script used to generate them.
- The static GitHub Pages site, manuscript figures, and compressed rollout GIFs.

## Excluded

- Raw laboratory videos or other identifiable recordings.
- Record-level robot trials, virtual rollout logs, reconstruction
  measurements, structure-error records, and ablation records.
- Pretrained and fine-tuned checkpoints, licensed upstream source trees, and
  locally installed simulator assets.
- Word and LaTeX manuscripts, EndNote libraries, PPT working files, revision
  notes, temporary outputs, and unrelated projects.
- Drawer-task records, which are outside the current evaluation scope.

## Validation Before Push

Run from the repository root:

```bash
python -m pip install -e ".[dev,figures]"
python -m pytest
```

The release is ready to push only when:

- every test passes;
- every local `src` and `href` used by `docs/index.html` resolves;
- the staged Git file list contains no secret, private path, manuscript, model
  checkpoint, raw video, or unrelated-project artifact;
- the project page is checked at desktop and mobile widths.

## GitHub Settings After Push

1. Keep the default branch named `main`.
2. Configure GitHub Pages to deploy from `main` and `/docs`.
3. Enable issues only if public bug reports are intended.
4. Add repository topics such as `3d-gaussian-splatting`, `robot-learning`,
   `sparse-demonstrations`, and `embodied-ai`.
5. Create an archival release only after the manuscript-facing commit has been
   assigned a stable version tag.
