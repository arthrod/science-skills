# Search Functions

Detailed argument specifications, output schemas, search strategies, and
troubleshooting for `search_papers`, `get_paper`, and `get_paper_results`.

## 1. `search_papers` — Find papers by query

Searches the Papers With Code database for papers matching a free-text query.
Results are paginated and include paper IDs (slugs) that can be passed to
`get_paper`, `get_paper_results`, `get_paper_code`, or `get_datasets`.

```bash
uv run scripts/pwc_api.py ./search_results.json search_papers "transformer attention" --limit 5
```

**Arguments:**

-   `query` (str, required) – free-text search query
-   `limit` (int, default 50) – maximum results to return (max ~500)

**Output:** A dict with pagination metadata and a `results` list:

```
{
  "count": 150,
  "next": "https://paperswithcode.com/api/v1/papers/?page=2",
  "previous": null,
  "results": [
    {
      "id": "attention-is-all-you-need",
      "title": "Attention Is All You Need",
      "abstract": "The dominant sequence transduction models...",
      "url_abs": "https://arxiv.org/abs/1706.03762",
      "url_pdf": "https://arxiv.org/pdf/1706.03762.pdf",
      "pwc_url": "https://paperswithcode.com/paper/attention-is-all-you-need",
      "published": "2017-06-12",
      "authors": [
        {"given_name": "Ashish", "family_name": "Vaswani"},
        ...
      ]
    }
  ]
}
```

**Common patterns:**

-   Extract paper IDs for chaining:
    ```bash
    cat ./search_results.json | jq -r '.results[].id'
    ```
-   Slim to title and URL:
    ```bash
    cat ./search_results.json | jq '[.results[] | {id, title, url: .url_abs}]'
    ```

**Search tips:**

-   Use concise, specific queries ("image segmentation", "BERT fine-tuning").
-   Boolean operators, quotes, and field filters are not officially documented;
    rely on natural language queries.
-   If search returns few results, try broader or alternate terms.

---

## 2. `get_paper` — Get paper details

Retrieves detailed metadata for a single paper by its PWC paper ID (the slug
from the URL, e.g. `attention-is-all-you-need`).

```bash
uv run scripts/pwc_api.py ./paper.json get_paper "attention-is-all-you-need"
```

**Arguments:**

-   `paper_id` (str, required) – the paper slug from paperswithcode.com

**Output:** A dict with paper fields:

```
{
  "id": "attention-is-all-you-need",
  "title": "Attention Is All You Need",
  "abstract": "The dominant sequence transduction models...",
  "url_abs": "https://arxiv.org/abs/1706.03762",
  "url_pdf": "https://arxiv.org/pdf/1706.03762.pdf",
  "pwc_url": "https://paperswithcode.com/paper/attention-is-all-you-need",
  "published": "2017-06-12",
  "authors": [{"given_name": "Ashish", "family_name": "Vaswani"}],
  "publishing_info": {
    "published": "2017",
    "venue": "Advances in Neural Information Processing Systems 30"
  },
  "abstract": "...",
  "arXivId": "1706.03762"
}
```

**Chaining example:** Get a paper, then fetch its code repositories:
```bash
uv run scripts/pwc_api.py ./paper.json get_paper "attention-is-all-you-need"
PAPER_ID=$(cat ./paper.json | jq -r '.id')
uv run scripts/pwc_api.py ./code.json get_paper_code "$PAPER_ID"
```

---

## 3. `get_paper_results` — Get evaluation results for a paper

Retrieves evaluation results (leaderboard entries) associated with a paper.
Each result shows which task, dataset, and model were evaluated, and the
reported metrics.

```bash
uv run scripts/pwc_api.py ./results.json get_paper_results "attention-is-all-you-need"
```

**Arguments:**

-   `paper_id` (str, required) – paper slug

**Output:** A dict with `count` and `results`:

```
{
  "count": 5,
  "results": [
    {
      "task": {"id": "machine-translation", "name": "Machine Translation"},
      "dataset": {"id": "wmt-2014-english-german", "name": "WMT 2014 English-German"},
      "model": "Transformer (base)",
      "metrics": [
        {"name": "BLEU", "value": "27.3"}
      ],
      "paper": {"id": "attention-is-all-you-need", "title": "Attention Is All You Need"}
    }
  ]
}
```

**Slimming example:**
```bash
cat ./results.json | jq '[.results[] | {task: .task.name, dataset: .dataset.name, model, metrics}]'
```
