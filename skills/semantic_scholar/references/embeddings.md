# Embeddings & NLP Functions

Detailed argument specifications, output schemas, and usage guidance for
`get_paper_embeddings` and `get_tldr`.

## 1. `get_paper_embeddings` — SPECTER/SPECTER2 embeddings

Retrieves vector embeddings for papers using the SPECTER or SPECTER2 model.
These embeddings can be used for semantic similarity search, clustering, or
as features in downstream NLP tasks.

```bash
uv run scripts/semantic_scholar_api.py ./embeddings.json get_paper_embeddings '["CorpusId:215416146","CorpusId:649def34f8"]' --model specter2
```

**Arguments:**

| Argument   | Type  | Required | Default    | Description |
|------------|-------|----------|------------|-------------|
| `ids_json` | str   | yes      | —          | JSON array of S2 PaperIds |
| `model`    | str   | no       | `"specter2"` | Embedding model: `"specter"` or `"specter2"` |

**Output:** `list[object]` — one object per paper:

- `paperId` (str) — S2 PaperId
- `embedding` (object) — embedding data:
  - `model` (str) — model name (e.g. `"specter2"`)
  - `vector` (list[float]) — embedding vector (768 dimensions for SPECTER, 1024 for SPECTER2)

**Important**:
- SPECTER produces 768-dimensional vectors. SPECTER2 produces 1024-dimensional
  vectors.
- Embeddings are based on the paper's title and abstract. Papers without
  abstracts may have degraded embedding quality.
- Not all papers have precomputed embeddings. Papers without embeddings will
  have `null` in the `embedding` field.

**Using embeddings for similarity search:**

```bash
# Extract embedding vectors
cat ./embeddings.json | jq '[.[] | {paperId, vector: .embedding.vector}]'

# Check which papers have embeddings
cat ./embeddings.json | jq '[.[] | select(.embedding != null) | .paperId]'
```

--------------------------------------------------------------------------------

## 2. `get_tldr` — TLDR summaries for papers

Retrieves short, AI-generated TLDR (Too Long; Didn't Read) summaries for one
or more papers. TLDRs provide concise one-to-two-sentence summaries of paper
contributions.

```bash
uv run scripts/semantic_scholar_api.py ./tldr_results.json get_tldr '["CorpusId:215416146","CorpusId:649def34f8"]'
```

**Arguments:**

| Argument   | Type  | Required | Default | Description |
|------------|-------|----------|---------|-------------|
| `ids_json` | str   | yes      | —       | JSON array of S2 PaperIds |

**Output:** `list[object]` — one object per paper:

- `paperId` (str) — S2 PaperId
- `tldr` (object | null) — TLDR summary:
  - `model` (str) — the TLDR model used (e.g. `"tldr-v3"`)
  - `text` (str) — the TLDR summary text

**Important**:
- TLDRs are AI-generated and may not capture every nuance of the paper.
- Not all papers have TLDRs. Papers without TLDRs will have `null` in the
  `tldr` field.
- TLDRs are available primarily for English-language papers.
- If a TLDR is not available, fall back to reading the abstract instead.

**Example workflow — search, get TLDRs:**

```bash
# Step 1: Search for papers
uv run scripts/semantic_scholar_api.py ./search.json search_papers "reinforcement learning robotics" --limit 5

# Step 2: Extract paper IDs
IDS=$(cat ./search.json | jq -c '[.[].paperId]')

# Step 3: Get TLDRs
uv run scripts/semantic_scholar_api.py ./tldrs.json get_tldr "$IDS"

# Step 4: View TLDR summaries
cat ./tldrs.json | jq '[.[] | select(.tldr != null) | {paperId, summary: .tldr.text}]'
```
