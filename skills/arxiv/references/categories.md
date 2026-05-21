# Categories & Bulk Functions

Detailed argument specifications, output schemas, and usage guidance for
`list_categories` and `get_recent_papers`.

## 1. `list_categories` — List all arXiv categories

Returns a curated list of all major arXiv subject categories, organized by group
(Computer Science, Mathematics, Physics, Quantitative Biology, Quantitative
Finance, Statistics, Electrical Engineering and Systems Science, Economics).

```bash
uv run scripts/arxiv_api.py ./categories.json list_categories
```

**Arguments:** None

**Output:** `list[object]` — one object per category:

| Field         | Type   | Description                                    |
|---------------|--------|------------------------------------------------|
| `id`          | str    | Category ID (e.g., "cs.CL", "q-bio.GN")       |
| `description` | str    | Human-readable description                     |
| `group`       | str    | Subject group (e.g., "Computer Science")       |

**Filtering by group with jq:**

```bash
# List all Computer Science categories
cat ./categories.json | jq '[.[] | select(.group == "Computer Science")]'

# List only q-bio categories
cat ./categories.json | jq '[.[] | select(.group == "Quantitative Biology")]'

# Find a specific category
cat ./categories.json | jq '[.[] | select(.id == "cs.CL")]'
```

### Major Category Groups Reference

| Group                                   | Example Categories                                    |
|-----------------------------------------|------------------------------------------------------|
| Computer Science                        | cs.AI, cs.CL, cs.CV, cs.LG, cs.IR, cs.RO           |
| Mathematics                             | math.CO, math.DS, math.NT, math.PR, math.ST        |
| Physics                                 | hep-th, quant-ph, astro-ph, cond-mat, gr-qc          |
| Quantitative Biology                    | q-bio.GN, q-bio.BM, q-bio.NC, q-bio.PE              |
| Quantitative Finance                    | q-fin.CP, q-fin.EC, q-fin.MF, q-fin.ST              |
| Statistics                              | stat.ML, stat.ME, stat.AP, stat.TH                   |
| Electrical Engineering & Systems Science| eess.AS, eess.IV, eess.SP, eess.SY                   |
| Economics                               | econ.EM, econ.GN, econ.TH                            |

---

## 2. `get_recent_papers` — Most recent submissions

Returns the most recent submissions to arXiv, optionally filtered by category.
Results are sorted by `submittedDate` descending (newest first).

```bash
# All recent papers (across all categories)
uv run scripts/arxiv_api.py ./recent_all.json get_recent_papers --limit 10

# Recent papers in a specific category
uv run scripts/arxiv_api.py ./recent_cs_cl.json get_recent_papers "cs.CL" --limit 25
uv run scripts/arxiv_api.py ./recent_genomics.json get_recent_papers "q-bio.GN" --limit 20
```

**Arguments:**

-   `category` (str or null, optional) – arXiv category to filter by
    (e.g., `"cs.CL"`, `"cs.AI"`, `"q-bio.GN"`). If omitted or empty, returns
    papers across all categories.
-   `limit` (int, default 50) – maximum number of results to return

**Output:** `list[object]` — array of paper metadata dicts, same schema as
`search_papers`:

| Field             | Type         | Description                                    |
|-------------------|--------------|------------------------------------------------|
| `id`              | str          | arXiv ID                                       |
| `title`           | str          | Paper title                                    |
| `summary`         | str          | Abstract                                       |
| `published`       | str          | ISO 8601 publication date                      |
| `updated`         | str          | ISO 8601 last updated date                     |
| `authors`         | list[str]    | List of author names                           |
| `pdf_url`         | str          | PDF download URL                               |
| `arxiv_url`       | str          | Abstract page URL                              |
| `primary_category`| str          | Primary subject category                       |
| `categories`      | list[str]    | All subject categories                         |
| `doi`             | str or null  | External DOI                                   |
| `journal_ref`     | str or null  | Journal reference                              |
| `comment`         | str or null  | Author comments                                |

### Usage Patterns

**List just titles and IDs of recent papers:**

```bash
uv run scripts/arxiv_api.py ./recent.json get_recent_papers "cs.AI" --limit 10
cat ./recent.json | jq '[.[] | {id, title}]'
```

**Count papers by primary category:**

```bash
cat ./recent.json | jq '[group_by(.primary_category)[] | {category: .[0].primary_category, count: length}]'
```

**Find papers with PDF links for download:**

```bash
cat ./recent.json | jq '[.[] | {id, pdf_url}]'
```
