# Private Data Interface

The public repository does not contain record-level robot trials, virtual
rollout logs, reconstruction measurements, structure-error records, or
ablation records. These files remain outside Git because they contain
laboratory-operation records and experiment-specific provenance.

The public validation and plotting utilities are retained as reusable code.
They operate only on a path supplied explicitly by the user:

```bash
python scripts/validate_paper_csvs.py --data /path/to/private/result-records
python scripts/plot_iteration_results.py \
  --data /path/to/private/iteration-results.csv \
  --output-dir outputs/iteration_figures
```

The validator checks required columns, count-rate identities, nonempty inputs,
and task-scope constraints. It does not download, infer, reconstruct, or repair
experimental values.

The manuscript defines the reported metrics, denominators, aggregation units,
and statistical protocol. Public code can be tested without access to the
private records by running:

```bash
python -m pytest
```

Raw camera video, Gaussian point clouds, USDZ assets, checkpoints, and
record-level experimental files are not stored in this Git repository.
