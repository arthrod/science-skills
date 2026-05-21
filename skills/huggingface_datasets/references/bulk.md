# Bulk & Stats Functions

Detailed argument specifications, output schemas, and workflow recipes for
`list_datasets_by_language`, `get_dataset_downloads`, and
`list_trending_datasets`.

## 1. `list_datasets_by_language` — Filter datasets by language

Lists datasets that match a specific language code. Useful for finding
datasets available in a target language.

```bash
uv run scripts/hf_datasets_api.py ./en_results.json list_datasets_by_language "en" --limit 10
```

**Arguments:**

-   `language` (str, required) – language code (e.g. `en`, `fr`, `de`, `es`,
    `zh`, `ja`, `ar`, `multilingual`)
-   `limit` (int, default 20) – maximum results to return

**Output:** `list[object]` — each object contains:

-   `id` (str) – dataset identifier
-   `description` (str) – dataset description
-   `downloads` (int) – total download count
-   `likes` (int) – number of likes
-   `tags` (list[str]) – all tags
-   `lastModified` (str) – ISO date of last modification

**Example: Find French-language datasets by keyword:**

```bash
uv run scripts/hf_datasets_api.py ./fr_results.json list_datasets_by_language "fr" --limit 20
cat ./fr_results.json | jq -r '.[].id'
```

--------------------------------------------------------------------------------

## 2. `get_dataset_downloads` — Get dataset popularity stats

Retrieves download count and popularity statistics for a specific dataset.

```bash
uv run scripts/hf_datasets_api.py ./downloads.json get_dataset_downloads "squad"
```

**Arguments:**

-   `dataset_name` (str, required) – dataset identifier

**Output:** `object` with:

-   `dataset` (str) – dataset name
-   `downloads` (int) – total number of downloads
-   `likes` (int) – number of likes/hearts

**Usage example:**

```bash
uv run scripts/hf_datasets_api.py ./stats.json get_dataset_downloads "imdb"
cat ./stats.json | jq
```

Expected output:
```json
{
  "dataset": "imdb",
  "downloads": 12345678,
  "likes": 345
}
```

--------------------------------------------------------------------------------

## 3. `list_trending_datasets` — Most downloaded datasets

Lists the most popular datasets on Hugging Face, sorted by total download
count.

```bash
uv run scripts/hf_datasets_api.py ./trending.json list_trending_datasets --limit 10
```

**Arguments:**

-   `limit` (int, default 20) – maximum results to return

**Output:** `list[object]` — same schema as `list_datasets_by_language` output,
sorted by download count descending.

**Example: Get top 5 NLP datasets:**

```bash
uv run scripts/hf_datasets_api.py ./top5.json list_trending_datasets --limit 5
cat ./top5.json | jq -r '.[] | "\(.id): \(.downloads) downloads"'
```

--------------------------------------------------------------------------------

## Workflow Recipes

### Search → Inspect → Get Details → Download Parquet

```bash
# 1. Search for question-answering datasets
uv run scripts/hf_datasets_api.py ./qa_search.json search_datasets "question answering" --limit 5

# 2. Get full details on the first result
FIRST=$(cat ./qa_search.json | jq -r '.[0].id')
uv run scripts/hf_datasets_api.py ./first_dataset.json get_dataset "$FIRST"

# 3. List configurations
uv run scripts/hf_datasets_api.py ./configs.json list_dataset_configs "$FIRST"

# 4. Get Parquet URLs for the train split
uv run scripts/hf_datasets_api.py ./parquet_urls.json get_dataset_parquet_urls "$FIRST" --split train
```

### Find the best dataset for a task

```bash
# 1. List datasets by task, sorted by popularity
uv run scripts/hf_datasets_api.py ./text_classification.json list_datasets_by_task "text-classification" --limit 20

# 2. Check tags on the top result
TOP=$(cat ./text_classification.json | jq -r '.[0].id')
uv run scripts/hf_datasets_api.py ./tags.json get_dataset_tags "$TOP"
cat ./tags.json | jq '{dataset, languages, licenses, sizes}'
```

### Multi-language dataset discovery

```bash
# 1. Find multilingual datasets
uv run scripts/hf_datasets_api.py ./multilingual.json list_datasets_by_language "multilingual" --limit 10

# 2. Check download stats for each
for id in $(cat ./multilingual.json | jq -r '.[].id'); do
  uv run scripts/hf_datasets_api.py "./stats_${id//\//_}.json" get_dataset_downloads "$id"
done

# 3. Aggregate stats
cat ./stats_*.json | jq -s '[.[] | {dataset, downloads, likes}]'
```

### Bulk retrieval and data slimming

For larger result batches, avoid processing results iteratively. Use shell
pipelines to slim results in one turn:

```bash
# Fetch trending datasets and slim to essential fields
uv run scripts/hf_datasets_api.py ./trending_raw.json list_trending_datasets --limit 50
cat ./trending_raw.json | jq '[.[] | {id, downloads, likes, description: (.description // "")[:150]}]' > ./trending_slim.json
```

### Find datasets by common criteria

```bash
# Find English sentiment analysis datasets
uv run scripts/hf_datasets_api.py ./sentiment_en.json search_datasets "sentiment" --task text-classification --language en --limit 10
```
