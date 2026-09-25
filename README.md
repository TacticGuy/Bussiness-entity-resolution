# Business Entity Resolution

This repository solves the challenge using only the supplied train/test files.
The `dataset/` folder is the input data location. A live database is not required
by the challenge; export database rows to the TSV layout below before running.

## 1. Install dependencies

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
New-Item -ItemType Directory -Force output
```

The source files must contain these columns:

```text
entity_id  business_name  business_address  country
```

Use these paths:

```text
dataset/train/train_source1.tsv
dataset/train/train_source2.tsv
dataset/train/train_source3.tsv
dataset/train/train_ground_truth.tsv
dataset/test/test_source1.tsv
dataset/test/test_source2.tsv
dataset/test/test_source3.tsv
```

If the data starts in a database, export each source table as UTF-8 TSV with a
tab separator. Do not use external business lookup or enrichment services.

## 2. Build training candidates

The blocker creates a local SQLite index on disk, so it does not compare every
Source 1 row with every Source 2/3 row in memory.

```powershell
python blocking.py `
	--source1 dataset/train/train_source1.tsv `
	--source2 dataset/train/train_source2.tsv `
	--source3 dataset/train/train_source3.tsv `
	--out output/train_candidate_pairs.tsv `
	--index output/train_index.sqlite
```

## 3. Build features and train

```powershell
python features.py `
	--candidate output/train_candidate_pairs.tsv `
	--ground-truth dataset/train/train_ground_truth.tsv `
	--source1 dataset/train/train_source1.tsv `
	--source2 dataset/train/train_source2.tsv `
	--source3 dataset/train/train_source3.tsv `
	--out output/train_features.tsv

python train_model.py `
	--features output/train_features.tsv `
	--model-out output/matcher_model.joblib `
	--val-out output/val_features.tsv
```

## 4. Build test candidates and produce submission

```powershell
python blocking.py `
	--source1 dataset/test/test_source1.tsv `
	--source2 dataset/test/test_source2.tsv `
	--source3 dataset/test/test_source3.tsv `
	--out output/candidate_pairs.tsv `
	--index output/test_index.sqlite

python score_and_submit.py `
	--model output/matcher_model.joblib `
	--val-features output/val_features.tsv `
	--train-ground-truth dataset/train/train_ground_truth.tsv `
	--train-source1 dataset/train/train_source1.tsv `
	--test-candidates output/candidate_pairs.tsv `
	--test-source1 dataset/test/test_source1.tsv `
	--test-source2 dataset/test/test_source2.tsv `
	--test-source3 dataset/test/test_source3.tsv `
	--out output/matching_results.tsv
```

## 5. Validate

```powershell
python utils\validate_submission.py `
	--matching output\matching_results.tsv `
	--candidate output\candidate_pairs.tsv `
	--test-dir dataset\test
```

Submit `output/matching_results.tsv`. Include both output TSV files and the
source code in the final challenge package.