# Search & Discover Functions

Detailed argument specifications, output schemas, search strategies, and
troubleshooting for `search_datasets`, `get_dataset`, and
`list_datasets_by_task`.

## 1. `search_datasets` — Find datasets by query

Searches the Hugging Face Datasets Hub for datasets matching a free-text query.
Optionally filters by task category and/or language code.

```bash
uv run scripts/hf_datasets_api.py ./search_results.json search_datasets "question answering" --task text-classification --language en --limit 5
```

**Arguments:**

-   `query` (str, required) – search query string (matched against dataset names
    and descriptions)
-   `task` (str, default "") – filter by task category, e.g. `text-classification`,
    `question-answering`, `summarization`, `translation`, `text-generation`,
    `token-classification`, `fill-mask`
-   `language` (str, default "") – filter by language code, e.g. `en`, `fr`,
    `de`, `es`, `zh`, `multilingual`
-   `limit` (int, default 20) – maximum results to return

**Output:** `list[object]` — each object contains:

-   `id` (str) – dataset identifier (e.g. `"squad"`, `"imdb"`)
-   `description` (str) – dataset description
-   `downloads` (int) – total download count
-   `likes` (int) – number of likes
-   `tags` (list[str]) – all tags (languages, tasks, licenses, sizes)
-   `lastModified` (str) – ISO date of last modification

**Filtering tips:**

-   To find datasets for a specific NLP task: use the `--task` flag with the
    appropriate task category name.
-   To find datasets in a specific language: use the `--language` flag with the
    ISO language code.
-   To broaden results, omit both filters and use only the query string.

**Output fields for assessment:**

```bash
cat ./search_results.json | jq '[.[] | {id, description: (.description // "")[:200], downloads, likes}]'
```

--------------------------------------------------------------------------------

## 2. `get_dataset` — Get full dataset metadata

Retrieves the complete metadata for a specific dataset, including configs, tags,
download statistics, file listings, and card README content.

```bash
uv run scripts/hf_datasets_api.py ./dataset_info.json get_dataset "squad"
```

**Arguments:**

-   `dataset_name` (str, required) – dataset identifier (e.g. `squad`, `imdb`,
    `bigscience-data/P3`). The organization prefix is part of the identifier for
    community datasets (e.g. `bigscience-data/P3`, `google/c4`).

**Output:** `object` with full dataset metadata including:

-   `id` (str) – dataset identifier
-   `description` (str) – description text
-   `citation` (str or null) – BibTeX citation if available
-   `cardData` (object or null) – structured card metadata
-   `configs` (list[object]) – available dataset configurations
-   `downloads` (int) – total download count
-   `likes` (int) – number of likes
-   `tags` (list[str]) – all tags
-   `siblings` (list[object]) – file listings (data files, configs)
-   `lastModified` (str) – ISO timestamp of last modification

**Check key stats:**

```bash
cat ./dataset_info.json | jq '{id, downloads, likes, config_count: (.configs | length)}'
```

--------------------------------------------------------------------------------

## 3. `list_datasets_by_task` — Filter datasets by NLP task

Lists datasets that match a specific task category, such as text classification,
question answering, or summarization.

```bash
uv run scripts/hf_datasets_api.py ./task_results.json list_datasets_by_task "text-classification" --limit 10
```

**Arguments:**

-   `task` (str, required) – task category (e.g. `text-classification`,
    `question-answering`, `summarization`, `translation`, `text-generation`,
    `token-classification`, `fill-mask`, `sentence-similarity`)
-   `limit` (int, default 20) – maximum results to return

**Output:** `list[object]` — same schema as `search_datasets` output. Each
object has `id`, `description`, `downloads`, `likes`, `tags`, `lastModified`.

**Common task categories:**

-   `text-classification` — sentiment analysis, topic classification, etc.
-   `question-answering` — extractive/generative QA datasets
-   `summarization` — text summarization datasets
-   `translation` — machine translation datasets
-   `text-generation` — language modeling and generation
-   `token-classification` — NER, POS tagging, etc.
-   `fill-mask` — masked language modeling
-   `sentence-similarity` — semantic/textual similarity
-   `text2text-generation` — sequence-to-sequence tasks
-   `image-classification` — computer vision (not NLP but valid)

**Example: Find top question-answering datasets:**

```bash
uv run scripts/hf_datasets_api.py ./qa_results.json list_datasets_by_task "question-answering" --limit 10
cat ./qa_results.json | jq -r '.[].id'
```
