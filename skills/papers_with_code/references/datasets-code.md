# Datasets & Code Functions

Detailed argument specifications, output schemas, and usage for
`get_paper_code`, `get_datasets`, `search_datasets`, and `get_dataset`.

## 1. `get_paper_code` — Get code repositories for a paper

Retrieves code repository links (typically GitHub) associated with a paper.
Each repository entry includes the URL, framework, and star count.

```bash
uv run scripts/pwc_api.py ./code_repos.json get_paper_code "attention-is-all-you-need"
```

**Arguments:**

-   `paper_id` (str, required) – paper slug

**Output:** A dict with `count` and `results`:

```
{
  "count": 3,
  "results": [
    {
      "url": "https://github.com/tensorflow/tensor2tensor",
      "owner": "tensorflow",
      "name": "tensor2tensor",
      "description": "Library of deep learning models and datasets...",
      "framework": "TensorFlow",
      "stars": 15000,
      "is_official": true,
      "is_original": true
    },
    ...
  ]
}
```

**Common patterns:**

-   Get the official implementation URL:
    ```bash
    cat ./code_repos.json | jq -r '.results[] | select(.is_official) | .url'
    ```
-   List all URLs:
    ```bash
    cat ./code_repos.json | jq -r '.results[].url'
    ```

---

## 2. `get_datasets` — Get datasets used by a paper

Retrieves the datasets that are used to evaluate a paper's method.

```bash
uv run scripts/pwc_api.py ./datasets.json get_datasets "attention-is-all-you-need"
```

**Arguments:**

-   `paper_id` (str, required) – paper slug

**Output:** A dict with `count` and `results`:

```
{
  "count": 2,
  "results": [
    {
      "id": "wmt-2014-english-german",
      "name": "WMT 2014 English-German",
      "url": "https://paperswithcode.com/dataset/wmt-2014-english-german",
      "papers": [
        {"id": "attention-is-all-you-need", "title": "Attention Is All You Need"}
      ]
    },
    ...
  ]
}
```

**Extracting dataset IDs:**
```bash
cat ./datasets.json | jq -r '.results[].id'
```

---

## 3. `search_datasets` — Search datasets

Searches for datasets by query string.

```bash
uv run scripts/pwc_api.py ./dataset_search.json search_datasets "cifar" --limit 5
```

**Arguments:**

-   `query` (str, required) – free-text search query for datasets
-   `limit` (int, default 50) – maximum results to return

**Output:** A dict with pagination and `results`:

```
{
  "count": 5,
  "results": [
    {
      "id": "cifar-10",
      "name": "CIFAR-10",
      "url": "https://paperswithcode.com/dataset/cifar-10",
      "description": "The CIFAR-10 dataset consists of 60000 32x32 colour images...",
      "papers": [...],
      "tasks": [{"id": "image-classification", "name": "Image Classification"}]
    }
  ]
}
```

**Slimming:**
```bash
cat ./dataset_search.json | jq '[.results[] | {id, name, url}]'
```

---

## 4. `get_dataset` — Get dataset details

Retrieves details about a specific dataset, including papers that use it.

```bash
uv run scripts/pwc_api.py ./dataset.json get_dataset "cifar-10"
```

**Arguments:**

-   `dataset_id` (str, required) – dataset slug (e.g. `cifar-10`)

**Output:** A dict with dataset details:

```
{
  "id": "cifar-10",
  "name": "CIFAR-10",
  "url": "https://paperswithcode.com/dataset/cifar-10",
  "description": "The CIFAR-10 dataset consists of 60000 32x32 colour images...",
  "papers": [
    {"id": "paper-slug", "title": "Paper Title"},
    ...
  ],
  "tasks": [
    {"id": "image-classification", "name": "Image Classification"}
  ]
}
```

**Extracting paper IDs from a dataset:**
```bash
cat ./dataset.json | jq -r '.papers[].id'
```

**Chaining example — find dataset, then discover papers using it:**
```bash
uv run scripts/pwc_api.py ./dataset.json get_dataset "cifar-10"
cat ./dataset.json | jq -r '.papers[].id'
```
