---
name: acl-anthology
description: >-
  Search and explore NLP research literature via the ACL Anthology and
  PapersWithCode API. Covers top NLP venues (ACL, NAACL, EMNLP, COLING,
  EACL, etc.). Retrieve paper metadata, author bibliographies, volume
  listings, benchmark results, SOTA leaderboards, and linked code
  repositories for NLP research.
---

# ACL Anthology & PapersWithCode

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.
3.  **`PWC_API_KEY`** (optional): PapersWithCode API key for higher rate limits.
    Obtain one at https://paperswithcode.com/api/v1/doc/ by registering. The
    skill works without it but may encounter rate limits under heavy usage.
4.  **No API key needed** for ACL Anthology (open access).

If the variables are missing from `.env`, do NOT ask the user to paste them into
the chat (this would leak keys into the agent's context). Instead, give the user
these commands — **substituting `ENV_FILE` with the resolved literal path to the
`.env` file**:

```bash
printf "Enter PapersWithCode API key (typing hidden): " && read -s key && echo && echo "PWC_API_KEY=$key" >> "ENV_FILE" && echo "Saved."
```

The scripts load credentials automatically via `dotenv`. **NEVER** read,
print, or inspect the `.env` file or its variables (e.g. no `cat`, `grep`,
`echo`, `printenv`, or `os.environ.get` on keys). Credentials must stay
out of the agent's context.

This skill provides CLI access to the ACL Anthology XML API, the ACL Anthology
website, and the PapersWithCode REST API via `scripts/acl_api.py` — a single
CLI with 11 functions covering search, paper details, venue listings, author
bibliographies, benchmark results, and SOTA leaderboards.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/acl_api.py` which
    manages rate limits automatically and prevents API abuse. Querying the APIs
    any other way (e.g. via curl, wget, or hand-written code) is strictly
    forbidden.
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
-   `scripts/acl_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search.md` - Search ACL Anthology
    -   `paperswithcode.md` - PapersWithCode API
    -   `venues.md` - Venue listing and author search

## CLI Usage

```bash
uv run scripts/acl_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional; list arguments are
    passed as comma-separated strings without spaces.
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
# Search ACL Anthology
uv run scripts/acl_api.py ./acl_results.json search_acl "transformer reasoning" --limit 10
cat ./acl_results.json | jq '.[].title'

# Get a specific paper by Anthology ID
uv run scripts/acl_api.py ./paper.json get_acl_paper "P19-1010"
cat ./paper.json | jq '.title'

# Get all papers from a venue/year
uv run scripts/acl_api.py ./volume.json get_acl_volume "ACL" 2024
cat ./volume.json | jq '.[].title'

# Search PapersWithCode
uv run scripts/acl_api.py ./pwc_results.json search_pwc "large language model" --limit 5
cat ./pwc_results.json | jq '.[].title'

# Get SOTA results for a task
uv run scripts/acl_api.py ./sota.json get_task_sota "machine translation"
cat ./sota.json | jq '.sota.sota_bleu'

# Find papers by author
uv run scripts/acl_api.py ./author_papers.json get_author_papers "Noam Chomsky" --limit 5
```

### Context Management & Accuracy

When processing larger result sets (>10 papers):

1.  **Filter Early**: Use `jq` to verify titles and keywords in results *before*
    reading the full JSON into context.
2.  **Slimming**: Extract only `title`, `anthology_id`, and `year` unless
    explicitly instructed otherwise. Full author lists and abstracts contribute
    to noise.
3.  **Bulk Operations (N > 10)**: Avoid processing results one-by-one. Fetch
    all data in a **single turn** and use shell pipelines to slim the results
    before reading into context. This prevents turn exhaustion and context
    overflow.
4.  **Grounding**: Never use internal knowledge to provide specific identifiers
    (Anthology IDs, PWC IDs) if no results are found. Report the tool's output
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

### [Search ACL Anthology](references/search.md)

-   `search_acl` — Search ACL Anthology by title, author, or venue.
-   `get_acl_paper` — Get paper details by ACL Anthology ID (e.g., 'P19-1010').
-   `get_acl_volume` — List all papers in a venue/year volume (e.g., ACL 2024).

### [PapersWithCode](references/paperswithcode.md)

-   `search_pwc` — Search PapersWithCode for papers with associated code.
-   `get_paper_tasks` — Get tasks/benchmarks associated with a paper.
-   `get_task_sota` — Get the state-of-the-art results for a specific NLP task.
-   `get_paper_results` — Get evaluation results for a paper.
-   `get_paper_code` — Get code repository links for a paper.
-   `get_datasets` — Get datasets used by a paper.

### [Venues & Bulk](references/venues.md)

-   `list_acl_venues` — List all ACL venue codes.
-   `get_author_papers` — Find papers by author name in ACL Anthology.
