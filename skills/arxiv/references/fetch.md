# Fetch Functions

Detailed argument specifications, output schemas, and usage guidance for
`get_paper`, `get_paper_pdf_url`, `get_paper_source_url`, and
`get_multiple_papers`.

## 1. `get_paper` — Get paper metadata by arXiv ID

Retrieves full metadata for a single paper by its arXiv ID.

```bash
uv run scripts/arxiv_api.py ./paper_2305.10601.json get_paper "2305.10601"
uv run scripts/arxiv_api.py ./paper_with_version.json get_paper "2305.10601v1"
```

**Arguments:**

-   `arxiv_id` (str, required) – arXiv ID (e.g., `"2305.10601"`,
    `"2305.10601v1"`)

**Output (success):** `object` — single paper metadata dict:

| Field             | Type         | Description                                    |
|-------------------|--------------|------------------------------------------------|
| `id`              | str          | Full arXiv ID (including version if specified) |
| `title`           | str          | Paper title (whitespace-normalized)            |
| `summary`         | str          | Abstract text (whitespace-normalized)          |
| `published`       | str          | ISO 8601 publication date                      |
| `updated`         | str          | ISO 8601 last updated date (if present)        |
| `authors`         | list[str]    | List of author names                           |
| `pdf_url`         | str          | Direct PDF download URL                        |
| `arxiv_url`       | str          | arXiv abstract page URL                        |
| `primary_category`| str          | Primary subject category                       |
| `categories`      | list[str]    | All subject categories (if present)            |
| `doi`             | str or null  | External DOI (if available)                    |
| `journal_ref`     | str or null  | Journal reference (if published)               |
| `comment`         | str or null  | Author comments (if any)                       |

**Output (error):** `{"error": str, "endpoint": "query"}` — paper not found.

---

## 2. `get_paper_pdf_url` — Get PDF download URL

Returns the direct PDF download URL for a paper. First tries to extract it from
the API metadata, and falls back to constructing the standard URL
(`https://arxiv.org/pdf/{base_id}.pdf`).

```bash
uv run scripts/arxiv_api.py ./pdf_url.json get_paper_pdf_url "2305.10601"
cat ./pdf_url.json | jq '.pdf_url' -r
```

**Arguments:**

-   `arxiv_id` (str, required) – arXiv ID (e.g., `"2305.10601"`)

**Output (success):** `{"arxiv_id": str, "pdf_url": str}`

**Output (error):** `{"error": str, "endpoint": "query"}` — paper not found in API.

**Usage:** The returned URL can be used directly with tools like `wget` or
`curl` to download the PDF:

```bash
wget -O paper.pdf "$(cat ./pdf_url.json | jq -r '.pdf_url')"
```

---

## 3. `get_paper_source_url` — Get source (.tar.gz) URL

Returns the URL to download the LaTeX/TeX source of a paper as a .tar.gz
archive. The URL is constructed from the base arXiv ID.

```bash
uv run scripts/arxiv_api.py ./source_url.json get_paper_source_url "2010.11645"
```

**Arguments:**

-   `arxiv_id` (str, required) – arXiv ID (e.g., `"2010.11645"`)

**Output:** `{"arxiv_id": str, "source_url": str}`

The source URL follows the pattern:
`https://arxiv.org/e-print/{base_id}`

**Important:** Not all papers have source available. When downloading
source files, always extract into a dedicated directory:

```bash
mkdir -p paper_source
wget -O source.tar.gz "$(cat ./source_url.json | jq -r '.source_url')"
tar -xzf source.tar.gz -C paper_source
```

---

## 4. `get_multiple_papers` — Get metadata for multiple papers

Retrieves metadata for several papers at once in a single API call.

```bash
uv run scripts/arxiv_api.py ./multiple_papers.json get_multiple_papers "2305.10601,1706.03762,2010.11645"
```

**Arguments:**

-   `ids` (list[str], required) – comma-separated arXiv IDs

**Output:** `list[object]` — array of paper metadata dicts, same fields as
`get_paper`. Order matches the input ID order.

### Common Chaining Patterns

**Extract IDs from search results for batch fetch:**

```bash
uv run scripts/arxiv_api.py ./search.json search_papers "transformer" --limit 5
cat ./search.json | jq -r '[.[] | .id] | join(",")' > ./id_list.txt
uv run scripts/arxiv_api.py ./details.json get_multiple_papers "$(cat ./id_list.txt)"
```

**Slim metadata to essential fields:**

```bash
cat ./details.json | jq '[.[] | {id, title, primary_category, authors}]'
```

**Extract all PDF URLs:**

```bash
cat ./details.json | jq '[.[] | .pdf_url]'
```
