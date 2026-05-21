---
name: arxiv
description: >-
  Search arXiv for scientific preprints and publications. Fetch paper metadata,
  abstracts, PDF download URLs, and source file URLs. List categories and recent
  submissions. Interfaces the arXiv API (export.arxiv.org/api/query).
---

# arXiv API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **User Notification**: If LICENSE_NOTIFICATION.txt does not already exist in
    this skill directory then (1) prominently notify the user to check the terms
    at https://info.arxiv.org/help/api/index.html and to always check the
    license of the papers retrieved by the skill for any restrictions, then (2)
    create the file recording the notification text and timestamp.
3.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.
4.  **`USER_EMAIL`** (optional but recommended): Identifies the caller to arXiv
    as a contact for abuse. The arXiv API does not require an API key.

If the variables are missing from `.env`, do NOT ask the user to paste them into
the chat (this would leak keys into the agent's context). Instead, give the user
these commands — **substituting `ENV_FILE` with the resolved literal path to the
`.env` file**:

```bash
printf "Enter contact email: " && read email && echo "USER_EMAIL=$email" >> "ENV_FILE" && echo "Saved."
```

The scripts load credentials automatically via `dotenv`. **NEVER** read,
print, or inspect the `.env` file or its variables (e.g. no `cat`, `grep`,
`echo`, `printenv`, or `os.environ.get` on keys). Credentials must stay
out of the agent's context.

This skill provides CLI access to the arXiv API via
`scripts/arxiv_api.py` — a single CLI with 9 functions covering search, fetch,
categories, and recent submissions.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/arxiv_api.py` which
    manages rate limits automatically and prevents API abuse. The arXiv API
    enforces a maximum of 1 request per 3 seconds. Querying the API any other
    way (e.g. via curl, wget, or hand-written code) is strictly forbidden.
-   **JSON Processing**: Use `jq` to filter and transform JSON output (or python
    equivalents if `jq` is not available) to prevent hallucinations and context
    overflow.
-   **Temporary Files**: To avoid polluting the working directory with JSON
    files, use a temporary directory inside the current directory. When running
    multiple agents or tasks in parallel, ensure each uses a unique subdirectory
    name (e.g., `tmp_$TASK_ID/`) to avoid file collisions.
-   **Notification**: If this skill is used, ensure this is mentioned in the
    output AND list the URLs of all papers that were used in producing the
    output.

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/arxiv_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search.md`
    -   `fetch.md`
    -   `categories.md`

## CLI Usage

```bash
uv run scripts/arxiv_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional; list arguments are
    passed as comma-separated strings without spaces (e.g.
    `"2305.10601,1706.03762"`).
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/arxiv_api.py ./search_results.json search_papers "transformer attention" --limit 5
cat ./search_results.json | jq '.[]' -r
uv run scripts/arxiv_api.py ./paper_2305.10601.json get_paper "2305.10601"
cat ./paper_2305.10601.json | jq '.title' -r
```

## Essential Recipes

**Join arXiv IDs for the next call (most common chaining pattern):**

```bash
cat ./search_results.json | jq -r '[.[] | .id] | join(",")'
```

**Slim metadata to essential fields and truncate long abstracts:**

```bash
cat ./search_results.json | jq '[.[] | {id, title, snippet: (.summary // "")[:500]}]'
```

**Filter by category:**

```bash
cat ./search_results.json | jq '[.[] | select(.primary_category == "cs.CL")]'
```

### Context Management & Accuracy

When processing larger result sets (>10 papers):

1.  **Filter Early**: Use `jq` to verify keywords in titles/abstracts *before*
    reading the full JSON into context.
2.  **Slimming**: Extract only `id`, `title`, `summary`, and `primary_category`
    unless explicitly instructed otherwise.
3.  **Bulk Operations (N > 10)**: Avoid fetching or processing IDs one-by-one.
    Fetch all data in a **single turn** and use shell pipelines to slim the
    results before reading into context. This prevents turn exhaustion and
    context overflow.
4.  **Grounding**: Never use internal knowledge to provide specific identifiers
    (arXiv IDs, DOIs) if no results are found. Report the tool's output
    accurately to ensure results are grounded in the current database state.
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

### [Search](references/search.md)

-   `search_papers`: Search arXiv by free-text query.
-   `search_by_author`: Find papers by author name.
-   `search_by_category`: List new submissions in a category.

### [Fetch](references/fetch.md)

-   `get_paper`: Get paper metadata by arXiv ID.
-   `get_paper_pdf_url`: Get PDF download URL for a paper.
-   `get_paper_source_url`: Get source (.tar.gz) URL for a paper.
-   `get_multiple_papers`: Get metadata for multiple papers at once.

### [Categories & Bulk](references/categories.md)

-   `list_categories`: List all arXiv categories with descriptions.
-   `get_recent_papers`: Get most recent submissions, optionally filtered by category.
