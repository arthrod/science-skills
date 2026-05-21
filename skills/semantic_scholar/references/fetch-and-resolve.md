# Fetch & Resolve Functions

Detailed argument specifications, output schemas, and usage guidance for
`get_paper_details`, `get_bulk_papers`, `get_author_details`,
`get_paper_citations`, and `get_paper_references`.

## 1. `get_paper_details` — Full paper details

Retrieves full details for a single paper including abstract, authors, citations,
references, TLDR summary, and embedding vector.

```bash
uv run scripts/semantic_scholar_api.py ./paper_details.json get_paper_details "CorpusId:215416146"
```

**Arguments:**

| Argument   | Type  | Required | Default | Description |
|------------|-------|----------|---------|-------------|
| `paper_id` | str   | yes      | —       | S2 PaperId (e.g. `"CorpusId:215416146"` or `"649def34f..."`) |
| `fields`   | str   | no       | `"title,abstract,authors,year,venue,citationCount,referenceCount,tldr,embedding"` | Comma-separated response fields |

**Output:** `object` — paper details:

- `paperId` (str) — S2 PaperId
- `externalIds` (dict | null) — external IDs (DOI, ArXiv, PubMed, ACL)
- `title` (str) — paper title
- `abstract` (str | null) — paper abstract
- `authors` (list[object]) — each with `authorId` and `name`
- `year` (int | null) — publication year
- `publicationDate` (str | null) — ISO date string (e.g. `"2021-06-01"`)
- `venue` (str | null) — publication venue
- `journal` (object | null) — journal info with `name`, `pages`, `volume`
- `citationCount` (int) — number of citations
- `referenceCount` (int) — number of references
- `openAccessPdf` (object | null) — `{"url": str, "status": str}` or null
- `tldr` (object | null) — `{"model": str, "text": str}` or null (if in fields)
- `embedding` (object | null) — `{"model": str, "vector": list[float]}` or null (if in fields)
- `citations` (list[object]) — first page of citations (if in fields)
- `references` (list[object]) — first page of references (if in fields)

**Important**: Including `citations`, `references`, or `embedding` in the
fields list increases response size significantly. For large citation/reference
traversals, use `get_paper_citations` and `get_paper_references` instead.

--------------------------------------------------------------------------------

## 2. `get_bulk_papers` — Fetch multiple papers

Fetches multiple papers in a single POST request. More efficient than calling
`get_paper_details` individually for each paper.

```bash
uv run scripts/semantic_scholar_api.py ./bulk_papers.json get_bulk_papers '["CorpusId:215416146","CorpusId:649def34f8"]'
```

**Arguments:**

| Argument   | Type  | Required | Default | Description |
|------------|-------|----------|---------|-------------|
| `ids_json` | str   | yes      | —       | JSON array of S2 PaperIds |
| `fields`   | str   | no       | `"title,authors,year,venue,citationCount,abstract"` | Comma-separated response fields |

**Output:** `list[object]` — one object per paper. Papers that are not found
are returned as `null` in the array and filtered out of the result.

--------------------------------------------------------------------------------

## 3. `get_author_details` — Author profile

Retrieves author profile information including name, h-index, publication list,
and citation statistics.

```bash
uv run scripts/semantic_scholar_api.py ./author_details.json get_author_details "1741101"
```

**Arguments:**

| Argument    | Type  | Required | Default | Description |
|-------------|-------|----------|---------|-------------|
| `author_id` | str   | yes      | —       | S2 AuthorId (e.g. `"1741101"`) |
| `fields`    | str   | no       | `"name,hIndex,papers,paperCount,citationCount"` | Comma-separated response fields |

**Output:** `object` — author details:

- `authorId` (str) — S2 AuthorId
- `name` (str) — author name
- `hIndex` (int | null) — h-index
- `paperCount` (int) — total number of papers
- `citationCount` (int) — total citation count
- `papers` (list[object]) — list of papers (if in fields), each with:
  - `paperId` (str)
  - `title` (str)
  - `year` (int | null)
  - `citationCount` (int)

**Finding AuthorIds**: AuthorIds can be found from paper search results (each
author object includes an `authorId` field). Alternatively, you can search
by author name using the `search_papers` function with an author-focused query
(e.g. `"author_name transformer attention"`).

--------------------------------------------------------------------------------

## 4. `get_paper_citations` — Papers citing a paper

Retrieves a paginated list of papers that cite a given paper.

```bash
uv run scripts/semantic_scholar_api.py ./citations.json get_paper_citations "CorpusId:215416146" --limit 50
```

**Arguments:**

| Argument   | Type  | Required | Default | Description |
|------------|-------|----------|---------|-------------|
| `paper_id` | str   | yes      | —       | S2 PaperId |
| `limit`    | int   | no       | 100     | Maximum citations (max 1000) |
| `fields`   | str   | no       | `"title,authors,year,venue,citationCount"` | Fields for the citing paper |

**Output:** `list[object]` — each entry contains:

- `citingPaper` (object) — the citing paper with requested fields
- `contexts` (list[str] | null) — citation contexts (surrounding text snippets)
- `intents` (list[str] | null) — citation intents (if available)

**Chaining pattern** — extract citing paper IDs for further operations:
```bash
cat ./citations.json | jq -r '[.[].citingPaper.paperId]'
```

--------------------------------------------------------------------------------

## 5. `get_paper_references` — Papers referenced by a paper

Retrieves a paginated list of papers that are referenced by a given paper
(i.e., its bibliography).

```bash
uv run scripts/semantic_scholar_api.py ./references.json get_paper_references "CorpusId:215416146" --limit 50
```

**Arguments:**

| Argument   | Type  | Required | Default | Description |
|------------|-------|----------|---------|-------------|
| `paper_id` | str   | yes      | —       | S2 PaperId |
| `limit`    | int   | no       | 100     | Maximum references (max 1000) |
| `fields`   | str   | no       | `"title,authors,year,venue,citationCount"` | Fields for the referenced paper |

**Output:** `list[object]` — each entry contains:

- `citedPaper` (object) — the referenced paper with requested fields
- `contexts` (list[str] | null) — reference contexts (surrounding text snippets)
- `intents` (list[str] | null) — reference intents (if available)

**Chaining pattern** — extract referenced paper IDs:
```bash
cat ./references.json | jq -r '[.[].citedPaper.paperId]'
```
