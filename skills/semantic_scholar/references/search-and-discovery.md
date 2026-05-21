# Search & Discovery Functions

Detailed argument specifications, output schemas, search strategies, and
troubleshooting for `search_papers`, `search_by_ids`, and `get_recommendations`.

## 1. `search_papers` — Search papers by query

Searches the Semantic Scholar corpus by free-text query. Returns basic metadata
(PaperId, title, authors, year, venue, citation count, open access PDF).

```bash
uv run scripts/semantic_scholar_api.py ./search_results.json search_papers "transformer attention mechanisms" --limit 5
```

**Arguments:**

| Argument  | Type  | Required | Default | Description |
|-----------|-------|----------|---------|-------------|
| `query`   | str   | yes      | —       | Free-text search query |
| `limit`   | int   | no       | 10      | Maximum results (max 100) |
| `fields`  | str   | no       | `"title,authors,year,venue,citationCount,openAccessPdf"` | Comma-separated response fields |

**Output:** `list[object]` — one object per result:

- `paperId` (str) — Semantic Scholar PaperId (e.g. `"649def34f8..."`)
- `externalIds` (dict | null) — map of external IDs (DOI, ArXiv, PubMed, ACL)
- `title` (str) — paper title
- `authors` (list[object]) — each with `authorId` (str) and `name` (str)
- `year` (int | null) — publication year
- `venue` (str | null) — publication venue/journal name
- `citationCount` (int) — number of citations
- `openAccessPdf` (object | null) — `{"url": str, "status": str}` or null

**Important**: The Semantic Scholar search API returns a maximum of 100 results
per call. For larger result sets, use `search_papers_batch` for cursor-based
pagination.

**Filtering tips:**

Use `jq` to filter results after retrieval:
```bash
# Filter by minimum year
cat ./search_results.json | jq '[.[] | select((.year // 0) >= 2020)]'

# Filter papers with open access PDF
cat ./search_results.json | jq '[.[] | select(.openAccessPdf != null)]'

# Extract just paper IDs for chaining
cat ./search_results.json | jq -r '[.[].paperId]'
```

--------------------------------------------------------------------------------

## 2. `search_by_ids` — Lookup papers by external IDs

Looks up papers by external identifiers (DOIs, ArXiv IDs, PubMed IDs, ACL IDs,
or S2 PaperIds). Uses the batch POST endpoint for efficient multi-ID lookup.

```bash
uv run scripts/semantic_scholar_api.py ./lookup_results.json search_by_ids '["10.18653/v1/2021.acl-long.200","10.48550/arXiv.2005.00401"]' --id_type DOI
```

**Arguments:**

| Argument   | Type  | Required | Default | Description |
|------------|-------|----------|---------|-------------|
| `ids_json` | str   | yes      | —       | JSON array of IDs (e.g. `'["id1","id2"]'`) |
| `id_type`  | str   | no       | `"DOI"` | ID type: `DOI`, `ArXiv`, `PubMed`, `ACL`, `CorpusId`, `PaperId` |
| `fields`   | str   | no       | `"title,authors,year,venue,citationCount,openAccessPdf"` | Comma-separated response fields |

**Output:** `list[object]` — same format as `search_papers`, but only for
successfully resolved IDs. Unresolved IDs are silently omitted.

**Supported ID types:**

| ID type     | Prefix    | Example                        |
|-------------|-----------|--------------------------------|
| `DOI`       | `DOI:`    | `DOI:10.1234/abc`              |
| `ArXiv`     | `ArXiv:`  | `ArXiv:2005.00401`             |
| `PubMed`    | `PubMed:` | `PubMed:35113657`              |
| `ACL`       | `ACL:`    | `ACL:2021.acl-long.200`        |
| `CorpusId`  | `CorpusId:` | `CorpusId:215416146`         |
| `PaperId`   | (raw)     | `649def34f8f9e5a8e...`         |

--------------------------------------------------------------------------------

## 3. `get_recommendations` — Paper recommendations

Gets paper recommendations based on a seed paper. Uses the Semantic Scholar
Recommendations API to find related papers.

```bash
uv run scripts/semantic_scholar_api.py ./recommendations.json get_recommendations "CorpusId:215416146" --limit 10
```

**Arguments:**

| Argument   | Type  | Required | Default | Description |
|------------|-------|----------|---------|-------------|
| `paper_id` | str   | yes      | —       | S2 PaperId of the seed paper |
| `limit`    | int   | no       | 10      | Maximum recommendations (max 500) |

**Output:** `list[object]` — recommended papers, each with:

- `paperId` (str) — S2 PaperId
- `externalIds` (dict | null) — external IDs
- `title` (str) — paper title
- `authors` (list[object]) — author list
- `year` (int | null) — publication year
- `citationCount` (int) — citation count

**Important**: The recommendations API requires the paper to have at least one
citation or reference for meaningful recommendations. Papers with no citation
graph connections will return empty results.
