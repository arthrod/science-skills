# Bulk Workflows

Detailed argument specifications, output schemas, and common multi-step batch
patterns for `search_papers_batch` and `batch_export_metadata`.

## 1. `search_papers_batch` — Cursor-based pagination

Performs paginated search requests using offset-based pagination. Use this when
you need more than the 100-result limit of `search_papers`, or when you want to
systematically iterate through large result sets.

```bash
uv run scripts/semantic_scholar_api.py ./batch_page1.json search_papers_batch "reinforcement learning" --offset 0 --limit 100
uv run scripts/semantic_scholar_api.py ./batch_page2.json search_papers_batch "reinforcement learning" --offset 100 --limit 100
```

**Arguments:**

| Argument | Type  | Required | Default | Description |
|----------|-------|----------|---------|-------------|
| `query`  | str   | yes      | —       | Free-text search query |
| `offset` | int   | no       | 0       | Number of results to skip |
| `limit`  | int   | no       | 100     | Results per page (max 100) |

**Output:** `list[object]` — same format as `search_papers`. Each page contains
up to `limit` results.

**Important**:
- The Semantic Scholar search API limits pagination to the first ~10,000
  results for any query. Beyond that, results may be truncated.
- Increasing `offset` by large values may impact performance. For systematic
  crawling, use smaller page sizes (100) and iterate.
- The total number of matching results is available in the response headers
  but not in the JSON body. Use the result count as a heuristic.

**Iteration script pattern:**

```bash
# Step 1: Fetch first page and get an estimate of total results
uv run scripts/semantic_scholar_api.py ./page_0.json search_papers_batch "transformer architecture" --offset 0 --limit 100
RESULT_COUNT=$(cat ./page_0.json | jq 'length')

# Step 2: Fetch subsequent pages
OFFSET=100
while [ "$OFFSET" -lt 300 ] && [ "$RESULT_COUNT" -gt 0 ]; do
  uv run scripts/semantic_scholar_api.py "./page_${OFFSET}.json" search_papers_batch "transformer architecture" --offset $OFFSET --limit 100
  RESULT_COUNT=$(cat "./page_${OFFSET}.json" | jq 'length')
  OFFSET=$((OFFSET + 100))
done

# Step 3: Aggregate all paper IDs
cat ./page_*.json | jq -s 'add | [.[].paperId]' > ./all_ids.json
```

--------------------------------------------------------------------------------

## 2. `batch_export_metadata` — Bulk export from IDs

Exports detailed metadata for a list of paper IDs in a single batch call.
Designed for exporting structured data from large pre-existing ID lists.

```bash
uv run scripts/semantic_scholar_api.py ./export_results.json batch_export_metadata '["CorpusId:215416146","CorpusId:649def34f8","CorpusId:12345678"]'
```

**Arguments:**

| Argument   | Type  | Required | Default | Description |
|------------|-------|----------|---------|-------------|
| `ids_json` | str   | yes      | —       | JSON array of S2 PaperIds |
| `fields`   | str   | no       | `"title,authors,year,venue,citationCount,abstract,publicationDate"` | Comma-separated response fields |

**Output:** `list[object]` — one object per paper with requested fields.
Unresolved IDs are silently omitted.

**Important**: The batch endpoint can handle up to 500 IDs per request. For
larger lists, split into chunks and call multiple times.

--------------------------------------------------------------------------------

## Workflow Recipes

### Search → fetch details → extract key information

```bash
# 1. Search for papers
uv run scripts/semantic_scholar_api.py ./search.json search_papers "few-shot learning NLP" --limit 5

# 2. Extract paper IDs
IDS=$(cat ./search.json | jq -c '[.[].paperId]')

# 3. Fetch full details
uv run scripts/semantic_scholar_api.py ./details.json get_bulk_papers "$IDS"

# 4. Slim to essentials
cat ./details.json | jq '[.[] | {paperId, title, abstract: (.abstract // "")[:300], year, citationCount}]' > ./slim.json
```

### Search → citations → snowball exploration

```bash
# 1. Find a seed paper
uv run scripts/semantic_scholar_api.py ./seed.json search_papers "attention is all you need" --limit 1
SEED_ID=$(cat ./seed.json | jq -r '.[0].paperId')

# 2. Get papers that cite the seed paper
uv run scripts/semantic_scholar_api.py ./citing.json get_paper_citations "$SEED_ID" --limit 20

# 3. Extract citing paper IDs
CITING_IDS=$(cat ./citing.json | jq -c '[.[].citingPaper.paperId]')

# 4. Get TLDRs for citing papers
uv run scripts/semantic_scholar_api.py ./citing_tldrs.json get_tldr "$CITING_IDS"
```

### Author → papers → embeddings

```bash
# 1. Get author details and their papers
uv run scripts/semantic_scholar_api.py ./author.json get_author_details "1741101" --fields "name,papers"

# 2. Extract author's paper IDs
AUTHOR_PAPER_IDS=$(cat ./author.json | jq -c '[.papers[].paperId]')

# 3. Get embeddings for author's papers
uv run scripts/semantic_scholar_api.py ./author_embeddings.json get_paper_embeddings "$AUTHOR_PAPER_IDS" --model specter2
```

### Pagination → batch export (N > 100)

```bash
# 1. Collect all paper IDs via paginated search
uv run scripts/semantic_scholar_api.py ./p1.json search_papers_batch "protein language model" --offset 0 --limit 100
uv run scripts/semantic_scholar_api.py ./p2.json search_papers_batch "protein language model" --offset 100 --limit 100

# 2. Merge all IDs
cat ./p1.json ./p2.json | jq -s 'add | [.[].paperId]' > ./all_ids.json

# 3. Batch export metadata for all IDs (up to 500 per call)
uv run scripts/semantic_scholar_api.py ./full_export.json batch_export_metadata "$(cat ./all_ids.json | jq -c '.')"

# 4. Slim the results
cat ./full_export.json | jq '[.[] | {paperId, title, year, citationCount, abstract: (.abstract // "")[:200]}]' > ./slim_export.json
```
