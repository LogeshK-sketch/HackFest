# Dataset Attribution

**Dataset Name**: Engineering Aptitude Test Questions
**Source**: Kaggle
**Author**: Keith Zidan Dsouza
**URL**: [Engineering Aptitude Test Questions](https://www.kaggle.com/datasets/keithzidan/engineering-aptitude-test-questions)
**License**: Public / Educational use

## Processing Notes
- The dataset is loaded using pandas in `data/load_dataset.py`.
- Rows with missing/empty column values are dropped.
- Duplicates by `question_text` are removed.
- Valid answers are strictly 'A', 'B', 'C', 'D' (case-insensitive conversion applied).
- Difficulties (`easy`, `medium`, `hard`) are assigned conceptually by equal thirds of the dataset.
- Categories (`aptitude`, `logical`, `verbal`, `numerical`) are assigned using simple keyword matching heuristics.
- All valid questions are seeded to the database using `flask seed-questions`.
