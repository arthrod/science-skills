---
name: semantic-scholar
description: >-
  Search and retrieve academic papers, authors, citations, recommendations, and
  embeddings from the Semantic Scholar corpus. Covers all scientific disciplines
  with particular strength in computer science and NLP.
---

# Semantic Scholar API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **User Notification**: Notify the user to check the API terms of service at
    https://www.semanticscholar.org/product/api/tos before using this skill.
3.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.
4.  **`S2_API_KEY`** (optional): Raises the Semantic Scholar API rate limit from
    1 request/second to 100 requests/second. The skill works without it, but a
    key is recommended if the user plans many queries or encounters rate limits.
    The user can obtain one for free at
    https://www.semanticscholar.org/product/api/

If the variables are missing from `.env`, do NOT ask the user to paste them into
the chat (this would leak keys into the agent's context). Instead, give the user
these commands — **substituting `ENV_FILE` with the resolved literal path to the
`.env` file**:

```bash
printf "Enter S2 API key (typing hidden): " && read -s key && echo && echo "S2_API_KEY=$key" >> "ENV_FILE" && echo "Saved."
```

The scripts load credentials automatically via `dotenv`. **NEVER** read, print,
or inspect the `.env` file or its variables (e.g. no `cat`, `grep`, `echo`,
`printenv`, or `os.environ.get` on keys). Credentials must stay out of the
agent's context.

This skill provides CLI access to the Semantic Scholar API via
`scripts/semantic_scholar_api.py` — a single CLI with 12 functions covering
search, fetch, citations, references, embeddings, TLDRs, and bulk workflows.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/semantic_scholar_api.py`
    which manages API endpoints and authentication. Setting the `S2_API_KEY`
    environment variable raises the rate limit from 1 to 100 requests/second.
    Querying the API any other way (e.g. via curl, wget, or hand-written code)
    is strictly forbidden.
-   **JSON Processing**: Use `jq` to filter and transform JSON output (or python
    equivalents if `jq` is not available) to prevent hallucinations and context
    overflow.
-   **Temporary Files**: To avoid polluting the working directory with JSON
    files, use a temporary directory inside the current directory. When running
    multiple agents or tasks in parallel, ensure each uses a unique subdirectory
    name (e.g., `tmp_$TASK_ID/`) to avoid file collisions.
-   **Notification**: If this skill is used, ensure this is mentioned in the
    output AND list the URLs of all papers that were used in producing the
    output (e.g. `https://www.semanticscholar.org/paper/CorpusId`).

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/semantic_scholar_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search-and-discovery.md`
    -   `fetch-and-resolve.md`
    -   `embeddings.md`
    -   `bulk-workflows.md`

## CLI Usage

```bash
uv run scripts/semantic_scholar_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional; list arguments are
    passed as JSON array strings (e.g. `'["CorpusId:123","CorpusId:456"]'`).
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/semantic_scholar_api.py ./search_results.json search_papers "transformer attention mechanisms" --limit 5
cat ./search_results.json | jq '.[]'
uv run scripts/semantic_scholar_api.py ./paper_details.json get_paper_details "CorpusId:215416146"
cat ./paper_details.json | jq '.title'
```

## Essential Recipes

**Join S2 IDs for the next call (most common chaining pattern):**

```bash
cat ./search_results.json | jq -r '[.[].paperId] | join(",")'
```

**Slim paper results to essential fields:**

```bash
cat ./search_results.json | jq '[.[] | {paperId, title, year, citationCount}]'
```

**Filter by year range (null-safe):**

```bash
cat ./search_results.json | jq '[.[] | select((.year // 0) >= 2020)]'
```

### Context Management & Accuracy

When processing larger result sets (>10 papers):

1.  **Filter Early**: Use `jq` to verify keywords in titles *before* reading
    the full JSON into context.
2.  **Slimming**: Extract only `paperId`, `title`, `year` and `citationCount`
    fields unless explicitly instructed otherwise. Author lists and abstracts
    contribute to noise.
3.  **Bulk Operations (N > 10)**: Avoid fetching or processing IDs one-by-one.
    The API supports batch POST endpoints for bulk retrieval. Fetch all data
    in a **single turn** and use shell pipelines to slim the results before
    reading into context. This prevents turn exhaustion and context overflow.
4.  **Grounding**: Never use internal knowledge to provide specific identifiers
    (S2 IDs, DOIs) if no results are found. Report the tool's output accurately
    to ensure results are grounded in the current database state.
5.  **Search Termination**: When asked to find papers that may not exist, limit
    exploration to 3–5 high-quality, varied search queries. If no results match
    after these attempts, conclude that no papers meet the criteria rather than
    continuing to iterate — unless explicitly instructed to be thorough.

## Functions

> **⚠️ MANDATORY**: You **MUST** read the linked reference file for a function
> group **before calling any function** in that group. The tables below only
> describe *what* each function does — not *how* to call it. Argument names,
> argument order, flags, and output schemas are **only** documented in the
> reference files. **Do NOT guess or infer arguments from function names.** If
> you call a function without first reading its reference, you **will** produce
> incorrect invocations.

### [Search](references/search-and-discovery.md)

-   `search_papers`: Search papers by query. Returns PaperId, title, authors,
    year, venue, citationCount, openAccessPdf.
-   `search_by_ids`: Lookup papers by S2 IDs, DOIs, ArXiv IDs, PubMed IDs,
    ACL IDs.
-   `get_recommendations`: Get paper recommendations based on a seed paper.

### [Fetch & Resolve](references/fetch-and-resolve.md)

-   `get_paper_details`: Full paper details with abstract, TLDR, authors,
    citations, references, embedding.
-   `get_bulk_papers`: Fetch multiple papers in one POST.
-   `get_author_details`: Author profile with papers, stats, h-index.
-   `get_paper_citations`: Papers citing a given paper.
-   `get_paper_references`: Papers referenced by a given paper.

### [Embeddings & NLP](references/embeddings.md)

-   `get_paper_embeddings`: SPECTER/SPECTER2 embeddings for papers.
-   `get_tldr`: TLDR summaries for papers.

### [Bulk Workflows](references/bulk-workflows.md)

-   `search_papers_batch`: Cursor-based pagination for large search result sets.
-   `batch_export_metadata`: Bulk export metadata from a list of IDs.
