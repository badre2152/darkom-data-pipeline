# Data

The repository does not include the source CSV or generated datasets.

Place the raw Darkom source CSV anywhere on your machine and pass its path to the pipeline. The Bronze loader copies the source into `data/bronze/darkom_annonces_raw.csv` before processing.

Example:

```bash
make pipeline CSV=/path/to/darkom_annonces_raw.csv
```

Generated Silver and Gold CSV files stay local because the repository ignores CSV files under `data/`.
