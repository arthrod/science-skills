---
name: fred
description: >-
  Retrieve economic time series data from the Federal Reserve Economic Data
  (FRED) API. Search for economic series by keyword, fetch observations
  over custom date ranges, explore categories, releases, and tags, and
  discover related series. Interfaces the Federal Reserve Bank of St. Louis
  FRED API.
---

# FRED Economic Data API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.
3.  **`FRED_API_KEY`** (required): The FRED API requires a free API key. The
    user can obtain one for free by registering at https://fred.stlouisfed.org/
    (sign in → Account → API Key). The skill will NOT work without a key.

If the `FRED_API_KEY` is missing from `.env`, do NOT ask the user to paste it
into the chat (this would leak keys into the agent's context). Instead, give the
user this command — **substituting `ENV_FILE` with the resolved literal path to
the `.env` file**:

```bash
printf "Enter FRED API key (typing hidden): " && read -s key && echo && echo "FRED_API_KEY=$key" >> "ENV_FILE" && echo "Saved."
```

The scripts load credentials automatically via `dotenv`. **NEVER** read,
print, or inspect the `.env` file or its variables (e.g. no `cat`, `grep`,
`echo`, `printenv`, or `os.environ.get` on keys). Credentials must stay
out of the agent's context.

This skill provides CLI access to the FRED API via
`scripts/fred_api.py` — a single CLI with 11 functions covering search,
time series data, categories, releases, and tags.

## Core Rules

- **API Use**: Always use the provided wrapper `scripts/fred_api.py` which
  manages rate limits automatically and prevents API abuse. The FRED API rate
  limit is 120 requests per minute. Querying the API any other way (e.g. via
  curl, wget, or hand-written code) is strictly forbidden.
- **API Base**: All requests go to `https://api.stlouisfed.org/fred/`. Every
  request requires `api_key=FRED_API_KEY` from the environment, `format=json`,
  and `file_type=json`.
- **JSON Processing**: Use `jq` to filter and transform JSON output (or python
  equivalents if `jq` is not available) to prevent hallucinations and context
  overflow.
- **Temporary Files**: To avoid polluting the working directory with JSON
  files, use a temporary directory inside the current directory. When running
  multiple agents or tasks in parallel, ensure each uses a unique subdirectory
  name (e.g., `tmp_$TASK_ID/`) to avoid file collisions.
- **Notification**: If this skill is used, ensure this is mentioned in the
  output AND list the URLs of any series IDs that were used in producing the
  output (e.g. `https://fred.stlouisfed.org/series/GDP`).

## Structure of the skill folder

- `SKILL.md` - This file
- `scripts/fred_api.py` - The skill CLI
- `references/` - Directory with detailed function specifications
  - `search.md`
  - `data.md`
  - `categories-releases.md`

## CLI Usage

```bash
uv run scripts/fred_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

- **Positional Arguments**: Arguments are positional; list arguments are
  passed as comma-separated strings without spaces.
- **Flag Options**: Optional arguments can be passed as `--flag value` instead
  of positional args.
- **Output Handling**: On success, JSON is written to `output_file`. On error,
  the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/fred_api.py ./search_results.json search_series "GDP" --limit 5
cat ./search_results.json | jq '.[] | {id, title}'
uv run scripts/fred_api.py ./gdp_data.json get_series_observations "GDP" --start "2020-01-01" --end "2023-12-31"
cat ./gdp_data.json | jq '.observations[:3]'
```

## Essential Recipes

**Extract series IDs from search results for further queries:**

```bash
cat ./search_results.json | jq -r '.[].id'
```

**Get latest observation value from a series:**

```bash
cat ./data.json | jq '.observations[-1].value'
```

**Slim observations to essential fields:**

```bash
cat ./data.json | jq '.observations | map({date, value})'
```

### Context Management & Accuracy

1.  **Filter Early**: Use `jq` to verify results *before* reading full JSON
    into context.
2.  **Slimming**: Extract only relevant fields (`id`, `title`, `date`, `value`)
    unless explicitly instructed otherwise.
3.  **Grounding**: Never use internal knowledge to provide specific series IDs,
    values, or category IDs if no results are found. Report the tool's output
    accurately to ensure results are grounded in the current database state.
4.  **Search Termination**: When asked to find series that may not exist, limit
    exploration to 3–5 high-quality, varied search queries. If no results match
    after these attempts, conclude that no series meet the criteria rather than
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

- `search_series` — Find economic series by keyword.
- `get_series_info` — Metadata about a specific series.

### [Data](references/data.md)

- `get_series_observations` — Time series observations (values) for a series.
- `get_series_categories` — Categories that a series belongs to.
- `get_series_release` — Release info for a series.
- `get_series_tags` — Tags for a series.

### [Categories & Releases](references/categories-releases.md)

- `get_category` — Category tree / child categories.
- `get_category_series` — Series within a category.
- `get_releases` — All economic releases.
- `get_release` — A specific release.
