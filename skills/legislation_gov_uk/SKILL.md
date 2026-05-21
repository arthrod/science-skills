---
name: legislation-gov-uk
description: >-
  Search and retrieve UK legislation from legislation.gov.uk — the official
  home of UK primary and secondary legislation. Access full text of Acts,
  Statutory Instruments, Scottish Statutory Instruments, and Welsh Statutory
  Instruments. Search by keyword, year, type, agency, or geography. Track
  amendments and historical versions over time.
---

# UK Legislation API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **No API key required**: The legislation.gov.uk API is a free, public API
    with no authentication required.
3.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.

This skill provides CLI access to the UK legislation.gov.uk API via
`scripts/legislation_api.py` — a single CLI with 9 functions covering search,
retrieval, versioning, and filtering.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/legislation_api.py`
    which manages JSON content negotiation and error handling. Querying the API
    any other way (e.g. via curl, wget, or hand-written code) is strictly
    forbidden unless the wrapper does not support the operation.
-   **JSON Processing**: Use `jq` to filter and transform JSON output (or python
    equivalents if `jq` is not available) to prevent hallucinations and context
    overflow.
-   **Temporary Files**: To avoid polluting the working directory with JSON
    files, use a temporary directory inside the current directory. When running
    multiple agents or tasks in parallel, ensure each uses a unique subdirectory
    name (e.g., `tmp_$TASK_ID/`) to avoid file collisions.

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/legislation_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search.md`
    -   `year-type.md`
    -   `bulk.md`

## CLI Usage

```bash
uv run scripts/legislation_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional; list arguments are
    passed as comma-separated strings without spaces.
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
# Search for legislation
uv run scripts/legislation_api.py ./search_results.json search_legislation "climate change" --limit 5
cat ./search_results.json | jq '.results[:2]'

# Get full text of a specific legislation
uv run scripts/legislation_api.py ./ukpga_2023_1.json get_legislation "ukpga/2023/1"

# List available legislation types
uv run scripts/legislation_api.py ./types.json get_legislation_types --limit 10
```

## Essential Recipes

**Extract titles from search results:**
```bash
cat ./search_results.json | jq '[.results[] | {title, year, type}]'
```

**Count results:**
```bash
cat ./search_results.json | jq '.total_results'
```

**Chain search to full retrieval:**
```bash
uv run scripts/legislation_api.py ./climate_acts.json search_legislation "climate" --type "Acts" --limit 1
ID=$(cat ./climate_acts.json | jq -r '.results[0].id // empty')
if [ -n "$ID" ]; then uv run scripts/legislation_api.py ./full_act.json get_legislation "$ID"; fi
```

### Context Management & Accuracy

1.  **Filter Early**: Use `jq` to inspect result summaries *before* reading
    the full JSON into context.
2.  **Slimming**: Extract only `title`, `year`, and `type` fields unless
    explicitly instructed otherwise. Full legislation text can be very large.
3.  **Grounding**: Never use internal knowledge to provide specific legislation
    IDs or content if no results are found. Report the tool's output accurately
    to ensure results are grounded in the current database state.

## Functions

> **⚠️ MANDATORY**: You **MUST** read the linked reference file for a function
> group **before calling any function** in that group. The tables below only
> describe *what* each function does — not *how* to call it. Argument names,
> argument order, flags, and output schemas are **only** documented in the
> reference files. **Do NOT guess or infer arguments from function names.** If
> you call a function without first reading its reference, you **will** produce
> incorrect invocations.

### [Search](references/search.md)

- `search_legislation`: Search UK legislation by keyword query.
- `get_legislation`: Full text of a specific piece of legislation.
- `get_legislation_types`: List available legislation types (Acts, SI, etc.).

### [By Year & Type](references/year-type.md)

- `get_legislation_by_year`: All legislation from a given year.
- `get_legislation_changes`: Amendments and changes over time for a piece of legislation.
- `get_legislation_versions`: Available versions (historical and current) of legislation.

### [Bulk](references/bulk.md)

- `get_legislation_by_type`: Filter legislation by type (Acts, SI, etc.).
- `get_legislation_by_agency`: Legislation by UK government department/agency.
- `search_by_geography`: Legislation applicable to a specific geography (England, Scotland, Wales, NI, UK).
