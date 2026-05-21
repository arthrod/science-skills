---
name: huggingface-datasets
description: >-
  Search the Hugging Face Datasets Hub for machine learning datasets. Discover
  datasets by query, task, or language. Retrieve dataset metadata,
  configurations, and Parquet download URLs. Browse tags, stats, and
  trending datasets.
---

# Hugging Face Datasets API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.
3.  **`HF_API_KEY`** (optional): A Hugging Face API token allows higher rate
    limits and access to gated/private datasets. The skill works without it
    for public datasets. The user can obtain one for free at
    https://huggingface.co/settings/tokens.

If the variable is missing from `.env`, do NOT ask the user to paste it into
the chat (this would leak keys into the agent's context). Instead, give the user
these commands — **substituting `ENV_FILE` with the resolved literal path to the
`.env` file**:

```bash
printf "Enter HF API token (typing hidden): " && read -s key && echo && echo "HF_API_KEY=$key" >> "ENV_FILE" && echo "Saved."
```

The scripts load credentials automatically via `dotenv`. **NEVER** read,
print, or inspect the `.env` file or its variables (e.g. no `cat`, `grep`,
`echo`, `printenv`, or `os.environ.get` on keys). Credentials must stay
out of the agent's context.

This skill provides CLI access to the Hugging Face Datasets API via
`scripts/hf_datasets_api.py` — a single CLI with 10 functions covering search,
discovery, dataset details, Parquet URLs, tags, stats, and trending.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/hf_datasets_api.py`
    which manages rate limits automatically. Querying the API any other way
    (e.g. via curl, wget, or hand-written code) is strictly forbidden.
-   **JSON Processing**: Use `jq` to filter and transform JSON output (or python
    equivalents if `jq` is not available) to prevent hallucinations and context
    overflow.
-   **Temporary Files**: To avoid polluting the working directory with JSON
    files, use a temporary directory inside the current directory. When running
    multiple agents or tasks in parallel, ensure each uses a unique subdirectory
    name (e.g., `tmp_$TASK_ID/`) to avoid file collisions.
-   **Notification**: If this skill is used, ensure this is mentioned in the
    output AND list the dataset names and URLs of all datasets that were used
    in producing the output.

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/hf_datasets_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search.md`
    -   `details.md`
    -   `bulk.md`

## CLI Usage

```bash
uv run scripts/hf_datasets_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional.
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/hf_datasets_api.py ./search_results.json search_datasets "question answering" --limit 3
cat ./search_results.json | jq '.[].id' -r

uv run scripts/hf_datasets_api.py ./dataset_info.json get_dataset "squad"
cat ./dataset_info.json | jq '.downloads, .likes'

uv run scripts/hf_datasets_api.py ./configs.json list_dataset_configs "squad"
cat ./configs.json | jq '.[].config_name' -r
```

## Essential Recipes

**Extract dataset IDs for chaining:**

```bash
cat ./search_results.json | jq -r '[.[].id] | join(",")'
```

**Slim dataset search results to essential fields:**

```bash
cat ./search_results.json | jq '[.[] | {id, description: (.description // "")[:200], downloads, likes}]'
```

**Find datasets by language and slim:**

```bash
cat ./search_results.json | jq '[.[] | select(.id | test("french|fr", "i"))]'
```

### Context Management & Accuracy

When processing larger result sets (>10 datasets):

1.  **Filter Early**: Use `jq` to verify dataset names and descriptions *before*
    reading the full JSON into context.
2.  **Slimming**: Extract only `id`, `description` (truncated), and `downloads`
    unless explicitly instructed otherwise. Full tag lists and card data
    contribute to noise.
3.  **Bulk Operations**: Avoid fetching or processing datasets one-by-one.
    The API supports search and list endpoints with pagination. Fetch all data
    in a **single turn** and use shell pipelines to slim the results before
    reading into context.
4.  **Grounding**: Never use internal knowledge to provide specific dataset
    names or statistics if no results are found. Report the tool's output
    accurately to ensure results are grounded in the current API state.
5.  **Search Termination**: When asked to find datasets that may not exist,
    limit exploration to 3–5 high-quality, varied search queries. If no results
    match after these attempts, conclude that no datasets meet the criteria
    rather than continuing to iterate — unless explicitly instructed to be
    thorough.

## Functions

> **⚠️ MANDATORY**: You **MUST** read the linked reference file for a function
> group **before calling any function** in that group. The tables below only
> describe *what* each function does — not *how* to call it. Argument names,
> argument order, flags, and output schemas are **only** documented in the
> reference files. **Do NOT guess or infer arguments from function names.** If
> you call a function without first reading its reference, you **will** produce
> incorrect invocations.

### [Search & Discover](references/search.md)

-   `search_datasets`: Search datasets on Hugging Face by query, task, or language.
-   `get_dataset`: Retrieve metadata, configs, card info, and file listings for a dataset.
-   `list_datasets_by_task`: Filter datasets by NLP task category.

### [Dataset Details](references/details.md)

-   `list_dataset_configs`: List available configurations/splits for a dataset.
-   `get_dataset_parquet_urls`: Get Parquet download URLs for direct data access.
-   `get_dataset_card`: Get dataset README/card markdown content.
-   `get_dataset_tags`: Get tags grouped by languages, tasks, licenses, and sizes.

### [Bulk & Stats](references/bulk.md)

-   `list_datasets_by_language`: List datasets filterable by language code.
-   `get_dataset_downloads`: Get download count and popularity stats.
-   `list_trending_datasets`: Most downloaded datasets on Hugging Face.
