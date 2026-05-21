# Journals & Funders Functions

Detailed argument specifications, output schemas, and usage guidance for
`search_journals`, `get_journal`, `search_funders`, and `get_funder`.

## 1. `search_journals` — Search CrossRef journals

Returns a list of journals matching a free-text query or ISSN. Use this to
discover journals registered with CrossRef, their ISSNs, and publisher
information.

```bash
uv run scripts/crossref_api.py ./journals_nature.json search_journals "Nature" --limit 10
uv run scripts/crossref_api.py ./journals_by_issn.json search_journals "0092-8674" --limit 5
```

**Arguments:**

-   `query` (str, required) — journal title, keyword, or ISSN search string
-   `limit` (int, default 20) — maximum results to return

**Output:** `list[object]` — each journal object contains:

-   `title` (str) — journal title
-   `ISSN` (list[str]) — print and online ISSN(s)
-   `publisher` (str | null) — publisher name
-   `publisher-location` (str | null) — publisher location
-   `subjects` (list[str]) — subject categories
-   `coverage` (list[str]) — coverage tags (e.g. `"current"`)
-   `breakdowns` (object) — publication count by year/type
-   `counts` (object) — total counts (dois, current, backfile)
-   `flags` (object) — journal flags (e.g. `deposits`, `abstracts`)
-   `languages` (list[str]) — publication languages

**Usage tip**: Get ISSNs for cross-referencing:

```bash
cat ./journals_nature.json | jq '[.[] | {title, issn: .ISSN}]'
```

---

## 2. `get_journal` — Journal metadata by ISSN

Retrieves detailed metadata for a single journal by its ISSN. Includes article
counts, coverage, subject areas, and publisher information.

```bash
uv run scripts/crossref_api.py ./journal_0092_8674.json get_journal "0092-8674"
```

**Arguments:**

-   `issn` (str, required) — ISSN of the journal (e.g. `"0092-8674"` for Cell)

**Output:** `object` — journal metadata with all fields from `search_journals`
but with full details, including:

-   `title` (str) — journal title
-   `ISSN` (list[str]) — print and online ISSN(s)
-   `publisher` (str | null) — publisher name
-   `publisher-location` (str | null) — publisher city
-   `subjects` (list[str]) — subject category labels
-   `coverage` (list[str]) — coverage tags (e.g. `"current"`, `"backfile"`)
-   `breakdowns` (object) — detailed publication counts
    -   `dois-by-issued-year` (list[list]) — yearly DOI counts
-   `counts` (object) — summary counts
    -   `total-dois` (int) — total DOIs registered
    -   `current` (int) — current (recent) DOIs
    -   `backfile` (int) — historical DOIs
-   `flags` (object) — capability flags
    -   `deposits` (bool) — journal currently deposits
    -   `abstracts` (bool) — journal deposits abstracts
    -   `funders` (bool) — journal deposits funding info
    -   `references` (bool) — journal deposits references
    -   `orcid` (bool) — journal supports ORCID
    -   `license` (bool) — journal deposits license info
-   `languages` (list[str]) — ISO language codes

---

## 3. `search_funders` — Search funding organizations

Returns a list of funding organizations matching a query string. Use this to
find funder IDs (DOI prefixes like `10.13039/...`) for use with `get_funder`.

```bash
uv run scripts/crossref_api.py ./funders_nih.json search_funders "National Institutes of Health" --limit 10
uv run scripts/crossref_api.py ./funders_nsf.json search_funders "National Science Foundation" --limit 5
```

**Arguments:**

-   `query` (str, required) — funder name search string
-   `limit` (int, default 20) — maximum results to return

**Output:** `list[object]` — each funder object contains:

-   `id` (str) — funder DOI (e.g. `"10.13039/100000002"`)
-   `name` (str) — funder name
-   `uri` (str) — funder URI
-   `location` (object | null) — funder location
    -   `country` (str | null) — country name
    -   `state` (str | null) — state/province
-   `alt-names` (list[str]) — alternative names/acronyms
-   `descendants` (list[str]) — child funder IDs
-   `hierarchy` (list[str]) — parent funder path
-   `replaces` (list[str]) — funder IDs this replaces
-   `replaced-by` (list[str]) — funder ID that replaces this one
-   `tokens` (list[str]) — search tokens

**Usage tip**: To find the funder ID for use with `get_funder`:

```bash
cat ./funders_nih.json | jq '[.[] | {id, name}]'
```

---

## 4. `get_funder` — Funder metadata by ID

Retrieves detailed metadata for a funding organization by its CrossRef funder
ID. Use this to get the funder's full name, location, alternate names, and
hierarchical relationships.

```bash
uv run scripts/crossref_api.py ./funder_100000002.json get_funder "10.13039/100000002"
```

**Arguments:**

-   `funder_id` (str, required) — funder DOI (e.g. `"10.13039/100000002"` for
    NIH)

**Output:** `object` — funder metadata, including:

-   `id` (str) — funder DOI
-   `name` (str) — official funder name
-   `uri` (str) — funder URI
-   `location` (object | null) — location information
-   `alt-names` (list[str]) — alternative names (acronyms, previous names)
-   `descendants` (list[str]) — child/descendant funder DOIs
-   `hierarchy` (list[str]) — hierarchy path to top-level parent
-   `replaces` (list[str]) — funder IDs this funder supersedes
-   `replaced-by` (list[str]) — funder ID that supersedes this one
-   `tokens` (list[str]) — search tokens for matching

**Usage tip**: Combine with `search_works` filtering to find works funded by a
specific organization:

```bash
uv run scripts/crossref_api.py ./nih_funded.json search_works "cancer" --filter "funder:10.13039/100000002" --limit 10
```
