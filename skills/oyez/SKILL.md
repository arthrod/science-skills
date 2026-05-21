---
name: oyez
description: >-
  Search and retrieve U.S. Supreme Court cases, oral arguments, and
  justice information via the free public Oyez.org API. Access case
  details by ID or docket number, fetch oral argument transcripts and
  audio URLs, explore justice biographies and voting records, and
  browse cases by Supreme Court term. No API key required.
---

# Oyez Supreme Court API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **User Notification**: The Oyez API (https://api.oyez.org/) is a free public
    API that does not require authentication. If the user plans to redistribute
    or publish data retrieved from this API, advise them to review Oyez's terms
    of use at https://www.oyez.org/about for any applicable restrictions.
3.  **No API Key Required**: The Oyez API is entirely free and open — no
    registration, API key, or environment variables are needed.

This skill provides CLI access to the Oyez.org Supreme Court API via
`scripts/oyez_api.py` — a single CLI with 10 functions covering case search,
case details, oral arguments, justice biographies, and term-based browsing.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/oyez_api.py` which
    manages rate limits automatically and prevents API abuse. Querying the API
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
    output AND list the Oyez URLs of all cases that were used in producing the
    output (e.g. https://www.oyez.org/cases/2023/22-1234).

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/oyez_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search.md`
    -   `oral-arguments.md`
    -   `justices-bulk.md`

## CLI Usage

```bash
uv run scripts/oyez_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional; list arguments are
    passed as comma-separated strings without spaces (e.g. `"12345,67890"`).
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
# Search for cases
uv run scripts/oyez_api.py ./search_results.json search_cases "free speech" --limit 5
cat ./search_results.json | jq '.[] | {name: .name, term: .term}'

# Get case details
uv run scripts/oyez_api.py ./case.json get_case "12345"
cat ./case.json | jq '.name, .docket_number'

# List all justices
uv run scripts/oyez_api.py ./justices.json list_justices
cat ./justices.json | jq '.[] | .name'

# Get cases by term
uv run scripts/oyez_api.py ./term_cases.json get_cases_by_term "2023" --limit 10
cat ./term_cases.json | jq '.[] | {name, docket_number}'
```

### Context Management & Accuracy

When processing larger result sets (>10 cases):

1.  **Filter Early**: Use `jq` to extract relevant fields *before* reading the
    full JSON into context.
2.  **Slimming**: Extract only `name`, `docket_number`, `term`, and `href`
    unless explicitly instructed otherwise. Full case details can be deep.
3.  **Bulk Operations (N > 10)**: Retrieve all data in a **single turn** and
    use shell pipelines to slim the results before reading into context. This
    prevents turn exhaustion and context overflow.
4.  **Grounding**: Never use internal knowledge to provide specific case IDs,
    docket numbers, or justice identifiers if no results are found. Report the
    tool's output accurately to ensure results are grounded in the current
    database state.

## Functions

> **⚠️ MANDATORY**: You **MUST** read the linked reference file for a function
> group **before calling any function** in that group. The tables below only
> describe *what* each function does — not *how* to call it. Argument names,
> argument order, flags, and output schemas are **only** documented in the
> reference files. **Do NOT guess or infer arguments from function names.** If
> you call a function without first reading its reference, you **will** produce
> incorrect invocations.

### [Search](references/search.md)

-   `search_cases` — Search Supreme Court cases by keyword or phrase.
-   `get_case` — Retrieve full details for a specific case by Oyez case ID.
-   `get_case_by_docket` — Look up a case by its docket number (e.g. "22-1234").

### [Oral Arguments](references/oral-arguments.md)

-   `get_oral_argument` — Retrieve the oral argument transcript for a case.
-   `get_oral_argument_audio` — Retrieve oral argument audio file URLs.
-   `search_oral_arguments_by_term` — Search oral arguments by Supreme Court term year.

### [Justices & Bulk](references/justices-bulk.md)

-   `get_justice` — Retrieve biography and voting record for a justice by name.
-   `list_justices` — List all Supreme Court justices (current and historical).
-   `get_justice_votes` — Retrieve voting record of a justice by name.
-   `get_cases_by_term` — Retrieve all cases heard in a specific Supreme Court term.
