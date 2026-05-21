---
name: world-bank
description: >-
  Query the World Bank API for country metadata, development indicators, and
  time-series economic data. Search countries and indicators, retrieve
  GDP/population/health/education time series for single or multiple countries,
  explore development topics, and get all-country snapshots for a given year.
  Free, no authentication required.
---

# World Bank API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.

2.  **User Notification**: If LICENSE_NOTIFICATION.txt does not already exist in
    this skill directory, then (1) prominently notify the user to check the
    terms at https://www.worldbank.org/en/about/legal and
    https://datacatalog.worldbank.org/public-licenses, then (2) create the file
    recording the notification text and timestamp.

3.  **No API key required**: The World Bank API is free and open. No
    authentication or environment variables are needed.

This skill provides CLI access to the World Bank API v2 via
`scripts/world_bank_api.py` — a single CLI with 10 functions covering country
search, indicator search, time-series data retrieval, and topic exploration.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/world_bank_api.py`
    which manages rate limits automatically and prevents API abuse. Querying
    the API any other way (e.g. via curl, wget, or hand-written code) is
    strictly forbidden.
-   **JSON Processing**: Use `jq` to filter and transform JSON output (or python
    equivalents if `jq` is not available) to prevent hallucinations and context
    overflow.
-   **Temporary Files**: To avoid polluting the working directory with JSON
    files, use a temporary directory inside the current directory. When running
    multiple agents or tasks in parallel, ensure each uses a unique subdirectory
    name (e.g., `tmp_$TASK_ID/`) to avoid file collisions.
-   **Notification**: If this skill is used, ensure this is mentioned in the
    output.

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/world_bank_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `countries-indicators.md`
    -   `data.md`
    -   `topics.md`

## CLI Usage

```bash
uv run scripts/world_bank_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional; list arguments are
    passed as comma-separated strings without spaces (e.g.
    `"US,GBR,DEU"`).
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/world_bank_api.py ./country.json get_country US
cat ./country.json | jq '.[]'

uv run scripts/world_bank_api.py ./data.json get_data US NY.GDP.MKTP.CD --start 2010 --end 2020
cat ./data.json | jq '[.[] | {year: .date, value: .value}]'

uv run scripts/world_bank_api.py ./gdp_all.json get_all_countries_data NY.GDP.MKTP.CD 2020
cat ./gdp_all.json | jq '[.[] | {country: .country.value, value: .value}]'
```

## Essential Recipes

**Filter results and extract key columns:**

```bash
cat ./data.json | jq '[.[] | {year: .date, value: .value, country: .country.value}]'
```

**Remove null values (missing data):**

```bash
cat ./data.json | jq '[.[] | select(.value != null) | {year: .date, value: .value}]'
```

**Sort by value descending:**

```bash
cat ./gdp_all.json | jq '[.[] | select(.value != null) | {country: .country.value, gdp: (.value | tonumber)}] | sort_by(.gdp) | reverse[:10]'
```

**Find indicator by keyword in name:**

```bash
cat ./indicators.json | jq '[.[] | select(.name | test("population"; "i")) | {id: .id, name: .name}]'
```

**Extract country name and capital from country metadata:**

```bash
cat ./country.json | jq '.[0] | {name: .name, capital: .capitalCity, region: .region.value, income: .incomeLevel.value}'
```

### Context Management & Accuracy

When processing larger result sets:

1.  **Filter Early**: Use `jq` to filter data *before* reading the full JSON
    into context.
2.  **Slimming**: Extract only the fields you need unless explicitly instructed
    otherwise.
3.  **Grounding**: Never use internal knowledge to provide specific indicator
    IDs or country codes if no results are found. Report the tool's output
    accurately to ensure results are grounded in the current database state.
4.  **Search Termination**: When asked to find indicators or countries that may
    not exist, limit exploration to 3–5 high-quality, varied search queries. If
    no results match after these attempts, conclude that nothing meets the
    criteria rather than continuing to iterate — unless explicitly instructed to
    be thorough.

## Functions

> **⚠️ MANDATORY**: You **MUST** read the linked reference file for a function
> group **before calling any function** in that group. The tables below only
> describe *what* each function does — not *how* to call it. Argument names,
> argument order, flags, and output schemas are **only** documented in the
> reference files. **Do NOT guess or infer arguments from function names.** If
> you call a function without first reading its reference, you **will** produce
> incorrect invocations.

### [Countries & Indicators](references/countries-indicators.md)

-   `get_country`: Get metadata for a single country by ISO code.
-   `search_countries`: Search countries by name.
-   `search_indicators`: Search available indicators by keyword and optional
    topic filter.
-   `get_indicator`: Get metadata for a single indicator by ID.

### [Data](references/data.md)

-   `get_data`: Get time series data for one country and one indicator.
-   `get_data_by_countries`: Get time series for multiple countries and one
    indicator.
-   `get_all_countries_data`: Get data for ALL countries for one indicator in a
    single year — ideal for cross-country comparisons.

### [Topics & Bulk](references/topics.md)

-   `list_topics`: List all available development topics.
-   `get_topic`: Get details for a single topic.
-   `get_country_indicators`: List all indicators available for a given country.
