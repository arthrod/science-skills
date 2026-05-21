---
name: crossref
---

# Crossref API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.
3.  **`USER_EMAIL`** (recommended): Provides your email to the Crossref Polite
    Pool, which offers higher rate limits and better service. The skill works
    without it, but adding it is recommended.
4.  **`CROSSREF_API_KEY`** (optional): Enables the Crossref Metadata Plus
    tier with additional features and higher rate limits. Obtain a key at
    https://www.crossref.org/services/metadata-plus/

If the variables are missing from `.env`, do NOT ask the user to paste them into
the chat (this would leak keys into the agent's context). Instead, give the user
these commands — **substituting `ENV_FILE` with the resolved literal path to the
`.env` file**:

```bash
printf "Enter contact email: " && read email && echo "USER_EMAIL=$email" >> "ENV_FILE" && echo "Saved."
```

```bash
printf "Enter Crossref API key (typing hidden): " && read -s key && echo && echo "CROSSREF_API_KEY=$key" >> "ENV_FILE" && echo "Saved."
```

The scripts load credentials automatically via `dotenv`. **NEVER** read,
print, or inspect the `.env` file or its variables (e.g. no `cat`, `grep`,
`echo`, `printenv`, or `os.environ.get` on keys). Credentials must stay
out of the agent's context.

This skill provides CLI access to the CrossRef REST API via
`scripts/crossref_api.py` — a single CLI with 10 functions covering work
search, journal and funder lookup, DOI agency resolution, and type
distribution analysis.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/crossref_api.py` which
    manages rate limits automatically and prevents API abuse. Setting the
    `USER_EMAIL` environment variable enables Polite Pool access with higher
    rate limits. Setting `CROSSREF_API_KEY` enables Metadata Plus features.
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
    output AND list the DOIs of all works that were used in producing the
    output.
-   **Citation Style**: When citing works from CrossRef, include the DOI as the
    canonical identifier. Always cite the source(s) used.

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/crossref_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search.md`
    -   `journals-funders.md`
    -   `bulk-metadata.md`

## CLI Usage

```bash
uv run scripts/crossref_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional.
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/crossref_api.py ./search_results.json search_works "deep learning" --limit 5
cat ./search_results.json | jq '.[] | {doi, title}'
uv run scripts/crossref_api.py ./work_metadata.json get_work "10.1038/nature12373"
cat ./work_metadata.json | jq '{title, author: .author[0].family, container: .["container-title"][0]}'
```

## Essential Recipes

**Get DOIs from search results (most common chaining pattern):**

```bash
cat ./search_results.json | jq -r '.[].DOI // empty'
```

**Get titles and first author from search results:**

```bash
cat ./search_results.json | jq '[.[] | {doi: .DOI, title: (.title[0] // ""), first_author: (.author[0].family // "")}]'
```

**Slim work metadata to essential fields:**

```bash
cat ./work_metadata.json | jq '{doi: .DOI, title: (.title[0] // ""), container: (.["container-title"][0] // ""), year: (.published["date-parts"][0][0]), type: .type}'
```

**Filter references with DOIs:**

```bash
cat ./references.json | jq '[.[] | select(.DOI != null)]'
```

### Context Management & Accuracy

When processing larger result sets (>10 works):

1.  **Filter Early**: Use `jq` to verify keywords in titles *before* reading
    the full JSON into context.
2.  **Slimming**: Extract only `DOI`, `title`, `container-title`, and
    `published-date` unless explicitly instructed otherwise. Author lists and
    full reference lists contribute to noise.
3.  **Bulk Operations (N > 10)**: Avoid fetching or processing DOIs one-by-one.
    The API supports bulk queries with `rows` parameter. Fetch all data in a
    **single turn** and use shell pipelines to slim the results before reading
    into context. This prevents turn exhaustion and context overflow.
4.  **Grounding**: Never use internal knowledge to provide specific identifiers
    (DOIs, ISSNs, funder IDs) if no results are found. Report the tool's output
    accurately to ensure results are grounded in the current database state.
5.  **Search Termination**: When asked to find works that may not exist, limit
    exploration to 3–5 high-quality, varied search queries. If no results match
    after these attempts, conclude that no works meet the criteria rather than
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

-   `search_works`: Search scholarly works by title, author, DOI, or keywords.
-   `get_work`: Retrieve full metadata for a work by DOI (title, authors,
    references, funding, ISSN, etc.).
-   `get_work_references`: Retrieve the reference list (cited works) for a DOIs.

### [Journals & Funders](references/journals-funders.md)

-   `search_journals`: Search journals by title or ISSN.
-   `get_journal`: Retrieve journal metadata and article counts by ISSN.
-   `search_funders`: Search funding organizations by name.
-   `get_funder`: Retrieve metadata for a specific funder by its ID.

### [Bulk & Metadata](references/bulk-metadata.md)

-   `get_agency`: Find which registration agency manages a given DOI.
-   `list_works_by_prefix`: List works registered under a specific DOI prefix.
-   `get_work_type_distribution`: Get the distribution of work types
    (journal-article, book-chapter, dataset, etc.) for a query.
