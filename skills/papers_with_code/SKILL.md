---
name: papers-with-code
description: >-
  Search Papers With Code for machine learning research papers, benchmark
  results, evaluation leaderboards, datasets, tasks, and associated code
  repositories. Track state-of-the-art results across ML tasks, discover
  datasets used by papers, and find code implementations linked to published
  work. Interfaces the Papers With Code API.
---

# Papers With Code API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.
3.  **`PWC_API_KEY`** (optional): A Papers With Code API token that raises rate
    limits and is recommended for heavy usage. The skill works without it. The
    user can obtain one by registering at https://paperswithcode.com/api/v1/
4.  **`USER_EMAIL`** (optional): An email address that may be required for
    higher rate limits.

If the variables are missing from `.env`, do NOT ask the user to paste them into
the chat (this would leak keys into the agent's context). Instead, give the user
these commands — **substituting `ENV_FILE` with the resolved literal path to the
`.env` file**:

```bash
printf "Enter Papers With Code API key (typing hidden): " && read -s key && echo && echo "PWC_API_KEY=$key" >> "ENV_FILE" && echo "Saved."
```

```bash
printf "Enter contact email: " && read email && echo "USER_EMAIL=$email" >> "ENV_FILE" && echo "Saved."
```

The scripts load credentials automatically via `dotenv`. **NEVER** read,
print, or inspect the `.env` file or its variables (e.g. no `cat`, `grep`,
`echo`, `printenv`, or `os.environ.get` on keys). Credentials must stay
out of the agent's context.

This skill provides CLI access to the Papers With Code API via
`scripts/pwc_api.py` — a single CLI with 10 functions covering paper search,
paper details, evaluation results, task search, task details, leaderboards,
code repositories, and datasets.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/pwc_api.py` which
    manages rate limits automatically and prevents API abuse. Setting the
    `PWC_API_KEY` environment variable adds an `Authorization` token to
    requests. Querying the API any other way (e.g. via curl, wget, or
    hand-written code) is strictly forbidden.
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
-   `scripts/pwc_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search.md`
    -   `tasks.md`
    -   `datasets-code.md`

## CLI Usage

```bash
uv run scripts/pwc_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional; list arguments are
    passed as comma-separated strings without spaces (e.g.
    `"paper1,paper2"`).
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/pwc_api.py ./search_results.json search_papers "transformer attention" --limit 5
cat ./search_results.json | jq '.results[:2] | .[].title' -r
uv run scripts/pwc_api.py ./paper.json get_paper "attention-is-all-you-need"
cat ./paper.json | jq '.title' -r
```

## Essential Recipes

**Extract paper IDs from search results for chain queries:**

```bash
cat ./search_results.json | jq -r '.results[].id'
```

**Get paper title, url_abs, and code URL:**

```bash
cat ./paper.json | jq '{title, url_abs: .url_abs, code: .pwc_url}'
```

**Slim leaderboard to top results:**

```bash
cat ./leaderboard.json | jq '[.results[:5] | .[] | {model, metric: .metrics[0].name, value: .metrics[0].value}]'
```

**Link paper to its code repository:**

```bash
uv run scripts/pwc_api.py ./code_repos.json get_paper_code "attention-is-all-you-need"
cat ./code_repos.json | jq '.results[].url'
```

### Context Management & Accuracy

When processing larger result sets (>10 items):

1.  **Filter Early**: Use `jq` to verify fields in results *before* reading
    the full JSON into context.
2.  **Slimming**: Extract only `id`, `title`, and key fields unless explicitly
    instructed otherwise. Full result objects with nested `metrics` or
    `repositories` contribute to noise.
3.  **Bulk Operations (N > 10)**: Fetch all data in a **single turn** and use
    shell pipelines to slim the results before reading into context. This
    prevents turn exhaustion and context overflow.
4.  **Grounding**: Never use internal knowledge to provide specific identifiers
    (paper IDs, task IDs, dataset IDs) if no results are found. Report the
    tool's output accurately to ensure results are grounded in the current
    database state.
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

-   `search_papers`: Search papers by query string.
-   `get_paper`: Get paper details including abstract and code link.
-   `get_paper_results`: Get evaluation results / leaderboard entries for a paper.

### [Tasks & Benchmarks](references/tasks.md)

-   `search_tasks`: Search ML tasks by query string.
-   `get_task`: Get task details, associated papers, and leaderboard.
-   `get_task_leaderboard`: Get the SOTA leaderboard for a task.

### [Datasets & Code](references/datasets-code.md)

-   `get_paper_code`: Get code repository links for a paper.
-   `get_datasets`: Get datasets used by a paper.
-   `search_datasets`: Search datasets by query string.
-   `get_dataset`: Get dataset details and papers using it.
