# Dataset Details Functions

Detailed argument specifications, output schemas, and usage guidance for
`list_dataset_configs`, `get_dataset_parquet_urls`, `get_dataset_card`,
and `get_dataset_tags`.

## 1. `list_dataset_configs` — List dataset configurations

Retrieves the available configurations (subsets/versions) and their split
details for a dataset. Many datasets have multiple configs (e.g. different
languages, difficulty levels, or processing modes).

```bash
uv run scripts/hf_datasets_api.py ./configs.json list_dataset_configs "squad"
```

**Arguments:**

-   `dataset_name` (str, required) – dataset identifier (e.g. `squad`, `imdb`,
    `bigscience-data/P3`)

**Output:** `list[object]` — each config object contains:

-   `config_name` (str) – name of the configuration (e.g. `"plain_text"`,
    `"v1.1"`, `"en"`)
-   `data_files` (list[object]) – data file entries with:
    -   `split` (str) – split name (e.g. `"train"`, `"test"`, `"validation"`)
    -   `path` (str) – relative file path within the dataset

**Check available configs and splits:**

```bash
cat ./configs.json | jq '[.[] | {config: .config_name, splits: [.data_files[].split] | unique}]'
```

--------------------------------------------------------------------------------

## 2. `get_dataset_parquet_urls` — Get Parquet download URLs

Returns direct download URLs for a dataset's Parquet files. Hugging Face
automatically converts datasets to Parquet format, which can be read directly by
DuckDB, Polars, Pandas, and other data tools without needing the `datasets`
library.

```bash
uv run scripts/hf_datasets_api.py ./parquet_urls.json get_dataset_parquet_urls "squad"
# Filter by config and split:
uv run scripts/hf_datasets_api.py ./parquet_urls.json get_dataset_parquet_urls "squad" --config plain_text --split train
```

**Arguments:**

-   `dataset_name` (str, required) – dataset identifier
-   `config` (str, default "") – optional config name to filter by
-   `split` (str, default "") – optional split name to filter by (`train`,
    `test`, `validation`)

**Output:** `list[str]` — list of Parquet file URLs. Each URL is a direct
download link to a `.parquet` file.

**Download a Parquet file and query with DuckDB:**

```bash
URL=$(cat ./parquet_urls.json | jq -r '.[0]')
curl -o data.parquet "$URL"
```

--------------------------------------------------------------------------------

## 3. `get_dataset_card` — Get dataset card README

Retrieves the dataset card (README) content, which contains descriptions,
intended uses, limitations, and licensing information written by the dataset
authors.

```bash
uv run scripts/hf_datasets_api.py ./card_data.json get_dataset_card "squad"
```

**Arguments:**

-   `dataset_name` (str, required) – dataset identifier

**Output:** `object` with:

-   `dataset` (str) – dataset name
-   `card` (str or null) – JSON-serialized card data if available, or empty
    string if no card exists

**Extract key card metadata:**

```bash
cat ./card_data.json | jq '.card | fromjson | {annotations_creators, language_creators, pretty_name}'
```

--------------------------------------------------------------------------------

## 4. `get_dataset_tags` — Get structured dataset tags

Returns tags for a dataset grouped by category: languages, tasks (annotations
creators), licenses, sizes, and other metadata.

```bash
uv run scripts/hf_datasets_api.py ./tags.json get_dataset_tags "squad"
```

**Arguments:**

-   `dataset_name` (str, required) – dataset identifier

**Output:** `object` with:

-   `dataset` (str) – dataset name
-   `languages` (list[str]) – language codes (e.g. `["en"]`, `["fr", "de"]`,
    `["multilingual"]`)
-   `tasks` (list[str]) – task categories (e.g. `["extractive-qa"]`,
    `["text-classification"]`)
-   `licenses` (list[str]) – license identifiers (e.g. `["cc-by-4.0"]`,
    `["mit"]`, `["apache-2.0"]`)
-   `sizes` (list[str]) – dataset size categories (e.g. `["n<1K"]`,
    `["1K<n<10K"]`, `["1M<n<10M"]`)
-   `other` (list[str]) – additional tags not fitting the above categories

**Quick language and license check:**

```bash
cat ./tags.json | jq '{dataset, languages, licenses}'
```
