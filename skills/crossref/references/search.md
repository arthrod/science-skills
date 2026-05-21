# Search Functions

Detailed argument specifications, output schemas, query strategies, and
troubleshooting for `search_works`, `get_work`, and `get_work_references`.

## 1. `search_works` — Search scholarly works

Returns a list of works matching a free-text query. Supports full CrossRef
query syntax including title, author, DOI, and keyword search.

### Query Tips

1.  **Simple keyword**: `search_works "quantum computing"` — searches across
    title, author, abstract, and metadata.
2.  **Structured query**: Use `query.title`, `query.author`, `query.container-title`
    parameters (via the `query` argument as a single string, or combine filters).
3.  **Filters**: The `filter` parameter accepts comma-separated `key:value`
    pairs. Common filters:
    -   `type:journal-article` — only journal articles
    -   `type:book-chapter` — only book chapters
    -   `type:dataset` — only datasets
    -   `has-references:t` — works that have references
    -   `has-abstract:t` — works with abstracts
    -   `has-orcid:t` — works with ORCID identifiers
    -   `from-pub-date:2020-01-01` — works published after a date
    -   `until-pub-date:2024-12-31` — works published before a date
    -   `member:1234` — works from a specific CrossRef member
    -   `prefix:10.1038` — works with a specific DOI prefix
4.  **Combining filters**: `type:journal-article,has-abstract:t,from-pub-date:2023-01-01`

### Search Strategies & Troubleshooting

If searching returns few or no results, try broadening before changing
strategy:

1.  **Drop field restrictions**: The base `query` parameter searches all
    metadata. If you got few results, try a broader query.
2.  **Use fewer filters**: Remove restrictive filters one at a time. `type:`
    filters are particularly restrictive — try omitting it.
3.  **Use structured query parameters**: CrossRef supports `query.title`,
    `query.author`, and `query.container-title` for field-specific searches.
    These can be combined via the filter parameter for more targeted results.
4.  **Check date ranges**: `from-pub-date` and `until-pub-date` filters use
    `YYYY-MM-DD` format. If no results, the date range may be too narrow.

### Usage

```bash
uv run scripts/crossref_api.py ./search_results.json search_works "deep learning" --limit 10
uv run scripts/crossref_api.py ./filtered_results.json search_works "CRISPR" --filter "type:journal-article,has-abstract:t" --limit 20
```

**Arguments:**

-   `query` (str, required) — free-text query searching across all metadata
-   `filter` (str, default "") — comma-separated `key:value` filter pairs
-   `limit` (int, default 20) — maximum results to return (max 1000)

**Output:** `list[object]` — each work object contains:

-   `DOI` (str) — Crossref DOI
-   `title` (list[str]) — title(s) of the work
-   `author` (list[object]) — authors with `family`, `given`, `ORCID`, etc.
-   `type` (str) — work type (e.g. `"journal-article"`, `"book-chapter"`)
-   `container-title` (list[str]) — journal or book title
-   `published-print` / `published-online` (object) — date parts
-   `publisher` (str) — publisher name
-   `abstract` (str | null) — abstract text if available
-   `subject` (list[str]) — subject categories
-   `ISSN` (list[str]) — ISSN(s) if applicable
-   `ISBN` (list[str]) — ISBN(s) if applicable
-   `member` (str) — CrossRef member ID
-   `reference-count` (int) — number of references
-   `is-referenced-by-count` (int) — citation count
-   `funder` (list[object]) — funding information if available
-   `license` (list[object]) — license information if available

### Filtering tips

-   **Only journal articles**: `--filter "type:journal-article"`
-   **Only works with abstracts**: `--filter "has-abstract:t"`
-   **Only works with references**: `--filter "has-references:t"`
-   **Date range**: `--filter "from-pub-date:2020-01-01,until-pub-date:2024-12-31"`
-   **Specific publisher**: `--filter "member:98"` (member ID for Elsevier)
-   **Combine**: `--filter "type:journal-article,has-abstract:t,from-pub-date:2023-01-01"`

---

## 2. `get_work` — Full work metadata by DOI

Retrieves the complete metadata record for a single work by its DOI. Returns
all available fields including title, authors, references, funding, ISSN, ISBN,
publisher, license, and abstract.

```bash
uv run scripts/crossref_api.py ./work_10_1038_nature12373.json get_work "10.1038/nature12373"
```

**Arguments:**

-   `doi` (str, required) — DOI of the work (e.g. `"10.1038/nature12373"`)

**Output:** `object` — full work metadata. Same structure as the items in
`search_works` but with all available fields, including:

-   All fields from `search_works` items above
-   `reference` (list[object]) — complete reference list (also available via
    `get_work_references`)
-   `link` (list[object]) — URLs to full text / landing pages
-   `update-to` / `update-from` (list[object]) — update relationships
-   `clinical-trial-number` (list[str]) — clinical trial registry numbers
-   `assertion` (list[object]) — publisher-specific assertions

**Important**: If the DOI is not found, the function returns an error with a
404 status. Verify the DOI format (e.g. `10.1038/nature12373` — *without* a
leading `https://doi.org/`).

---

## 3. `get_work_references` — Reference list for a work

Retrieves the list of references (works cited by the specified DOI). Each
reference may include a DOI, title, year, volume, issue, and page information.

```bash
uv run scripts/crossref_api.py ./references_10_1038_nature12373.json get_work_references "10.1038/nature12373"
```

**Arguments:**

-   `doi` (str, required) — DOI of the work whose references to retrieve

**Output:** `list[object]` — each reference object contains:

-   `DOI` (str | null) — DOI of the cited work (null if not registered)
-   `key` (str) — reference key used within the citing article
-   `unstructured` (str | null) — raw citation text
-   `author` (str) — first author surname
-   `year` (int | null) — publication year
-   `volume` (str | null) — journal volume
-   `issue` (str | null) — journal issue
-   `first-page` (str | null) — starting page
-   `article-title` (str | null) — title of the cited work
-   `journal-title` (str | null) — journal name
-   `series-title` (str | null) — series title for books
-   `doi-asserted-by` (str | null) — who asserted the DOI (`"crossref"` or
    `"publisher"`)

**Usage tip**: Filter references that have DOIs for further exploration:

```bash
cat ./references.json | jq '[.[] | select(.DOI != null)]'
```
