---
name: data-gov
description: >-
  Search and retrieve US government open data from Data.gov using the CKAN API.
  Discover datasets by keyword, organization, topic, and file format. Access
  resource files, tags, and metadata for government datasets across all federal
  agencies. Free public API — no authentication required.
---

# Data.gov CKAN API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.

2.  **No authentication required**: The Data.gov CKAN API is a free public API.
    No API key, registration, or token is needed.

This skill provides CLI access to the Data.gov CKAN catalog API via
`scripts/data_gov_api.py` — a single CLI with 11 functions covering search,
dataset details, organizations, groups, resources, tags, and recent datasets.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/data_gov_api.py` which
    manages rate limits automatically. Querying the CKAN API any other way
    (e.g. via curl, wget, or hand-written code) is strictly forbidden.
-   **JSON Processing**: Use `jq` to filter and transform JSON output (or python
    equivalents if `jq` is not available) to prevent hallucinations and context
    overflow.
-   **Temporary Files**: To avoid polluting the working directory with JSON
    files, use a temporary directory inside the current directory. When running
    multiple agents or tasks in parallel, ensure each uses a unique subdirectory
    name (e.g., `tmp_$TASK_ID/`) to avoid file collisions.
-   **Notification**: If this skill is used, ensure this is mentioned in the
    output AND list the URLs of all datasets that were used.

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/data_gov_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search.md`
    -   `organizations.md`
    -   `resources-tags.md`

## CLI Usage

```bash
uv run scripts/data_gov_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional; pass them in the order
    shown in the function signature.
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/data_gov_api.py ./search_results.json search_datasets "climate change" --limit 5
cat ./search_results.json | jq '.[] | {title, organization: .organization.title}'

uv run scripts/data_gov_api.py ./dataset.json get_dataset "db24c0d1-2c29-4c76-9ceb-f5f36504978c"
cat ./dataset.json | jq '.resources[].url'

uv run scripts/data_gov_api.py ./orgs.json list_organizations
cat ./orgs.json | jq '.[].display_name'
```

### Context Management & Accuracy

1.  **Filter Early**: Use `jq` to extract only relevant fields (title,
    description, resource URLs) before reading the full JSON into context.
2.  **Slimming**: When processing lists of datasets, extract only `title`,
    `id`, and `organization.title` unless explicitly instructed otherwise.
3.  **Grounding**: Never use internal knowledge to provide specific dataset IDs
    or metadata. Report the tool's output accurately to ensure results are
    grounded in the current data catalog state.

## Functions

> **⚠️ MANDATORY**: You **MUST** read the linked reference file for a function
> group **before calling any function** in that group. The tables below only
> describe *what* each function does — not *how* to call it. Argument names,
> argument order, flags, and output schemas are **only** documented in the
> reference files. **Do NOT guess or infer arguments from function names.** If
> you call a function without first reading its reference, you **will** produce
> incorrect invocations.

### [Search](references/search.md)

-   `search_datasets` — Search US government datasets by keyword, topic, and file format
-   `get_dataset` — Retrieve full metadata for a dataset by its ID
-   `get_dataset_show` — Retrieve package details by ID or name

### [Organizations & Groups](references/organizations.md)

-   `get_organization` — Get agency/department details and their datasets
-   `list_organizations` — List all organizations on Data.gov
-   `get_group` — Get topic category details and its datasets
-   `list_groups` — List all groups (topics/categories)

### [Resources & Tags](references/resources-tags.md)

-   `get_resource` — Get details about a specific resource file
-   `search_tags` — Search datasets by keyword tag
-   `list_tags` — List all tags on Data.gov
-   `get_recent_datasets` — Get recently added or updated datasets
