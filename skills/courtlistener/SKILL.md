---
name: courtlistener
description: >-
  Search and retrieve U.S. federal and state court opinions, dockets, oral
  arguments, and judge information via the CourtListener Legal Research API.
  Free API key available at courtlistener.com/register (5000 req/day
  authenticated). Covers full-text opinion search, case lookup by docket
  number, judge/author opinions, and oral argument recordings.
---

# CourtListener Legal Research API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.
3.  **`COURTLISTENER_API_KEY`** (required): The skill needs a CourtListener API
    key to function. Get one for free by registering at
    https://www.courtlistener.com/register/ — the free tier allows 5000
    requests per day. The skill will work without a key but may hit rate
    limits quickly.

If the variable is missing from `.env`, do NOT ask the user to paste it into
the chat (this would leak keys into the agent's context). Instead, give the
user these commands — **substituting `ENV_FILE` with the resolved literal path
to the `.env` file**:

```bash
printf "Enter CourtListener API key (typing hidden): " && read -s key && echo && echo "COURTLISTENER_API_KEY=$key" >> "ENV_FILE" && echo "Saved."
```

The scripts load credentials automatically via `dotenv`. **NEVER** read,
print, or inspect the `.env` file or its variables (e.g. no `cat`, `grep`,
`echo`, `printenv`, or `os.environ.get` on keys). Credentials must stay out of
the agent's context.

This skill provides CLI access to the CourtListener REST API v4 via
`scripts/courtlistener_api.py` — a single CLI with 11 functions covering
opinion search, docket lookup, court/judge queries, and oral arguments.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/courtlistener_api.py`
    which manages rate limits automatically and prevents API abuse. Setting the
    `COURTLISTENER_API_KEY` environment variable authorizes up to 5000
    requests/day. Querying the API any other way (e.g. via curl, wget, or
    hand-written code) is strictly forbidden.
-   **JSON Processing**: Use `jq` to filter and transform JSON output (or python
    equivalents if `jq` is not available) to prevent hallucinations and context
    overflow.
-   **Temporary Files**: To avoid polluting the working directory with JSON
    files, use a temporary directory inside the current directory. When running
    multiple agents or tasks in parallel, ensure each uses a unique subdirectory
    name (e.g., `tmp_$TASK_ID/`) to avoid file collisions.

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/courtlistener_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `opinions.md`
    -   `dockets.md`
    -   `courts-judges.md`
    -   `oral-arguments.md`

## CLI Usage

```bash
uv run scripts/courtlistener_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional; list arguments are
    passed as comma-separated strings without spaces (e.g.
    `"ca1,ca2"`).
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/courtlistener_api.py ./search_results.json search_opinions "free speech" --court ca1 --limit 3
cat ./search_results.json | jq '.[].caseName' -r

uv run scripts/courtlistener_api.py ./opinion.json get_opinion_by_id 12345
cat ./opinion.json | jq '.caseName, .plain_text' -r

uv run scripts/courtlistener_api.py ./courts.json list_courts
cat ./courts.json | jq '.[] | {id, full_name}' -r
```

## Essential Recipes

**Extract case names and dates from opinion search results:**

```bash
cat ./search_results.json | jq '[.[] | {caseName, court, dateFiled}]'
```

**Get plain text of an opinion:**

```bash
cat ./opinion.json | jq -r '.plain_text' | head -100
```

**Filter opinions by court after search:**

```bash
cat ./search_results.json | jq '[.[] | select(.court | test("ca[0-9]"))]'
```

**Chain search into citation lookup:**

```bash
## Step 1: search opinions
uv run scripts/courtlistener_api.py ./opinions.json search_opinions "fourth amendment" --limit 1
## Step 2: extract opinion ID and fetch citations
OPINION_ID=$(cat ./opinions.json | jq '.[0].id')
uv run scripts/courtlistener_api.py ./citations.json get_opinion_citations "$OPINION_ID"
```

### Context Management & Accuracy

1.  **Filter Early**: Use `jq` to select specific fields from results *before*
    reading the full JSON into context.
2.  **Slimming**: Extract only `caseName`, `court`, `dateFiled`, and relevant
    text excerpts unless explicitly instructed otherwise.
3.  **Grounding**: Never use internal knowledge to provide specific case names,
    citations, or docket numbers if no results are found. Report the tool's
    output accurately to ensure results are grounded in the current database
    state.
4.  **Search Termination**: When asked to find cases that may not exist, limit
    exploration to 3–5 high-quality, varied search queries. If no results match
    after these attempts, conclude that no cases meet the criteria — unless
    explicitly instructed to be thorough.

## Functions

> **⚠️ MANDATORY**: You **MUST** read the linked reference file for a function
> group **before calling any function** in that group. The tables below only
> describe *what* each function does — not *how* to call it. Argument names,
> argument order, flags, and output schemas are **only** documented in the
> reference files. **Do NOT guess or infer arguments from function names.** If
> you call a function without first reading its reference, you **will** produce
> incorrect invocations.

### [Search Opinions](references/opinions.md)

-   `search_opinions`: Search full-text court opinions with optional court and
    date filters.
-   `get_opinion_by_id`: Get a specific opinion's full metadata by ID.
-   `get_opinion_citations`: Get citations to/from an opinion.

### [Dockets & Cases](references/dockets.md)

-   `search_dockets`: Search dockets by case name or query.
-   `get_docket_entries`: Get docket entries for a specific docket.
-   `get_docket_by_case_number`: Lookup a docket by case number and court.

### [Courts & Judges](references/courts-judges.md)

-   `list_courts`: List all available courts.
-   `search_judges`: Search judges by name and/or court.
-   `get_judge_opinions`: Get opinions authored by a specific judge.

### [Oral Arguments](references/oral-arguments.md)

-   `search_oral_arguments`: Search oral argument recordings.
-   `get_oral_argument`: Get oral argument metadata and download URL by ID.
