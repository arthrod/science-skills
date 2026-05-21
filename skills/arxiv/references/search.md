# Search Functions

Detailed argument specifications, output schemas, search strategies, and
troubleshooting for `search_papers`, `search_by_author`, and
`search_by_category`.

## 1. `search_papers` — Search arXiv by query

Returns a list of papers matching a free-text query. Supports full arXiv query
syntax including field prefixes, Boolean operators, grouping, and exact phrase
matching.

```bash
uv run scripts/arxiv_api.py ./search_results.json search_papers "transformer attention" --limit 5
```

**Arguments:**

-   `query` (str, required) – free-text query string
-   `limit` (int, default 20) – maximum number of results to return
-   `sort_by` (str, default "relevance") – `relevance`, `submittedDate`,
    or `lastUpdatedDate`

**Output:** `list[object]`

| Field             | Type         | Description                                    |
|-------------------|--------------|------------------------------------------------|
| `id`              | str          | arXiv ID (e.g., "2305.10601v1")               |
| `title`           | str          | Paper title (whitespace-normalized)            |
| `summary`         | str          | Abstract text (whitespace-normalized)          |
| `published`       | str          | ISO 8601 publication date                      |
| `updated`         | str          | ISO 8601 last updated date (if present)        |
| `authors`         | list[str]    | List of author names                           |
| `pdf_url`         | str          | Direct PDF download URL                        |
| `arxiv_url`       | str          | arXiv abstract page URL                        |
| `primary_category`| str          | Primary subject category (e.g., "cs.CL")       |
| `categories`      | list[str]    | All subject categories (if present)            |
| `doi`             | str or null  | External DOI (if available)                    |
| `journal_ref`     | str or null  | Journal reference (if published)               |
| `comment`         | str or null  | Author comments on the paper (if any)          |

### Query Syntax Reference

Use field prefixes to target specific parts of the paper record:

| Prefix  | Target Field    | Example                                       |
|---------|----------------|-----------------------------------------------|
| `ti:`   | Title          | `ti:transformer`                              |
| `au:`   | Author         | `au:einstein`                                 |
| `abs:`  | Abstract       | `abs:attention mechanism`                     |
| `co:`   | Comment        | `co:accepted`                                 |
| `jr:`   | Journal Ref    | `jr:Nature`                                   |
| `cat:`  | Category       | `cat:cs.CL`                                   |
| `rn:`   | Report Number  | `rn:1234`                                     |
| `all:`  | All fields     | `all:quantum computing` (default if omitted)  |

**Boolean Operators:** `AND`, `OR`, `ANDNOT`
- Example: `au:del_maestro ANDNOT ti:checkerboard`

**Grouping:** Parentheses `()` for complex boolean expressions
- Example: `(au:einstein OR au:hawking) AND ti:relativity`

**Phrases:** Double quotes for exact phrase matching
- Example: `ti:"attention is all you need"`

**Date Filtering:** Use `submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM]`
- Example: `cat:cs.CL AND submittedDate:[202301010600 TO 202401010600]`

### Search Strategies & Troubleshooting

If searching returns few or no results, try at most 3 queries before changing
strategy. After 3 failed searches, the query is flawed. Broaden to core concepts
and adopt vocabulary from the abstracts.

Relaxation order:

1.  **Drop Field Restrictors**: If you used `ti:` or `abs:` and got no results,
    use an unqualified (`all:`) query instead.
    -   Too restrictive: `ti:"deep learning" AND abs:"protein folding"`
    -   Better: `"deep learning" AND "protein folding"`

2.  **Use Broad Synonyms**: Group related terms with OR.
    -   Example: `(transformer OR "language model" OR LLM) AND (biology OR genomics)`

3.  **Remove Granular Constraints**: Drop the weakest constraint first (e.g.,
    date range, specific category).

4.  **Avoid Over-Quoting**: Double quotes force exact phrase matching. Use
    unquoted terms for conceptual matching.

### Filtering Tips in Queries

-   **Category filter:** `cat:cs.CL` (limit to a subject category)
-   **Author filter:** `au:"firstname lastname"` (find papers by a specific author)
-   **Date range:** append `AND submittedDate:[202301010600 TO 202401010600]`
-   **Exclude reviews:** use `ANDNOT ti:review`

---

## 2. `search_by_author` — Find papers by author

Searches for papers authored by a specific person. Wraps `search_papers` with
the `au:` prefix.

```bash
uv run scripts/arxiv_api.py ./einstein_papers.json search_by_author "Albert Einstein" --limit 10
```

**Arguments:**

-   `author_name` (str, required) – full or partial author name
-   `limit` (int, default 20) – maximum number of results to return

**Output:** Same as `search_papers` — `list[object]` with paper metadata.

---

## 3. `search_by_category` — List new submissions in a category

Lists recent papers submitted to a specific arXiv category, sorted by
`submittedDate` descending.

```bash
uv run scripts/arxiv_api.py ./recent_cs_cl.json search_by_category "cs.CL" --limit 10
uv run scripts/arxiv_api.py ./recent_genomics.json search_by_category "q-bio.GN" --limit 25
```

**Arguments:**

-   `category` (str, required) – arXiv category (e.g., `cs.CL`, `cs.AI`,
    `q-bio.GN`)
-   `limit` (int, default 50) – maximum number of results to return

**Output:** Same as `search_papers` — `list[object]` with paper metadata.
