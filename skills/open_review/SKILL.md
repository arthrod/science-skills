---
name: open-review
---

# OpenReview API

## Prerequisites

1.  **`uv`**: Read the `uv` skill and follow its Setup instructions to ensure
    `uv` is installed and on PATH.
2.  **`.env` file**: Make sure the `.env` file exists in your home directory.
    Create one if it does not exist.
3.  **`OPENREVIEW_API_KEY`** (optional): Enables access to private/anonymous
    content (e.g. review texts, author response, decision notifications).
    The skill works without it for public content. Obtain a free API key at
    https://openreview.net/login (login, go to Settings, and generate a key).

If the variable is missing from `.env`, do NOT ask the user to paste it into
the chat (this would leak keys into the agent's context). Instead, give the user
this command — **substituting `ENV_FILE` with the resolved literal path to the
`.env` file**:

```bash
printf "Enter OpenReview API key (typing hidden): " && read -s key && echo && echo "OPENREVIEW_API_KEY=$key" >> "ENV_FILE" && echo "Saved."
```

The scripts load credentials automatically via `dotenv`. **NEVER** read,
print, or inspect the `.env` file or its variables (e.g. no `cat`, `grep`,
`echo`, `printenv`, or `os.environ.get` on keys). Credentials must stay
out of the agent's context.

This skill provides CLI access to the OpenReview REST API via
`scripts/openreview_api.py` — a single CLI with 9 functions covering paper and
review search, venue discovery, forum thread retrieval, and group membership
lookup.

## Core Rules

-   **API Use**: Always use the provided wrapper `scripts/openreview_api.py`
    which manages rate limits automatically and prevents API abuse. Setting the
    `OPENREVIEW_API_KEY` environment variable enables access to private content
    (review ratings, author responses, decision notifications) that is hidden
    from unauthenticated requests. Querying the API any other way (e.g. via
    curl, wget, or hand-written code) is strictly forbidden.
-   **JSON Processing**: Use `jq` to filter and transform JSON output (or python
    equivalents if `jq` is not available) to prevent hallucinations and context
    overflow.
-   **Temporary Files**: To avoid polluting the working directory with JSON
    files, use a temporary directory inside the current directory. When running
    multiple agents or tasks in parallel, ensure each uses a unique subdirectory
    name (e.g., `tmp_$TASK_ID/`) to avoid file collisions.
-   **Notification**: If this skill is used, ensure this is mentioned in the
    output AND list the forum IDs or note IDs of all papers that were used in
    producing the output.
-   **Rate Limiting**: OpenReview does not publish a hard rate limit, but please
    keep requests to a reasonable pace (1–2 per second). If you encounter 429
    responses, back off and retry after a few seconds.

## Structure of the skill folder

-   `SKILL.md` - This file
-   `scripts/openreview_api.py` - The skill CLI
-   `references/` - Directory with detailed function specifications
    -   `search.md`
    -   `venues.md`
    -   `bulk.md`

## CLI Usage

```bash
uv run scripts/openreview_api.py <output_file> <function_name> <required_args> [--flag value ...]
```

-   **Positional Arguments**: Arguments are positional.
-   **Flag Options**: Optional arguments can be passed as `--flag value` instead
    of positional args.
-   **Output Handling**: On success, JSON is written to `output_file`. On error,
    the process exits with a non-zero code and no output file is written.

### Example Usage

```bash
uv run scripts/openreview_api.py ./search_results.json search_notes "transformer" --limit 5
cat ./search_results.json | jq '.[] | {id, title}'
uv run scripts/openreview_api.py ./note.json get_note "S3ff6d1234567890abcdef1234567890ab"
cat ./note.json | jq '{id, title, forum, venue}'
```

## Essential Recipes

**Get note IDs from search results (most common chaining pattern):**

```bash
cat ./search_results.json | jq -r '.[].id // empty'
```

**Get titles and venues from search results:**

```bash
cat ./search_results.json | jq '[.[] | {id, title: (.content.title // .content.paper_title // ""), venue: .content.venue}]'
```

**Get forum threads from a list of forum IDs:**

```bash
cat ./forums.txt | while read fid; do uv run scripts/openreview_api.py "./forum_${fid}.json" get_notes_by_forum "$fid"; done
```

**List all notes for a specific venue (e.g., ICLR 2024 submissions):**

```bash
uv run scripts/openreview_api.py ./venue_notes.json get_venue_notes "ICLR.cc/2024/Conference" --stage "Submission"
```

### Context Management & Accuracy

When processing larger result sets (>10 notes):

1.  **Filter Early**: Use `jq` to verify keywords in titles *before* reading
    the full JSON into context.
2.  **Slimming**: Extract only `id`, `forum`, `content.title`, and
    `content.venueid` unless explicitly instructed otherwise. Full review
    content and author lists contribute to noise.
3.  **Bulk Operations (N > 10)**: Avoid fetching or processing note IDs
    one-by-one. The API supports pagination with the `limit` parameter for
    search functions. Fetch all data in a **single turn** and use shell
    pipelines to slim the results before reading into context. This prevents
    turn exhaustion and context overflow.
4.  **Grounding**: Never use internal knowledge to provide specific identifiers
    (note IDs, forum IDs, venue IDs) if no results are found. Report the tool's
    output accurately to ensure results are grounded in the current database
    state.
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

-   `search_notes`: Search papers/reviews by query text.
-   `get_note`: Retrieve full details of a single note (paper, review, or
    comment) including its content.
-   `get_venue`: Retrieve metadata for a conference/venue.

### [Venues](references/venues.md)

-   `get_venue_notes`: Get papers/reviews by venue and submission stage.
-   `get_venue_groups`: Get the groups/committees associated with a venue.
-   `list_venues`: List available venues/conferences.

### [Bulk](references/bulk.md)

-   `search_notes_by_group`: Get notes (papers/reviews) authored by members of
    a specific group.
-   `get_notes_by_forum`: Get all notes in a forum thread (paper + reviews +
    decisions + comments).
-   `get_group`: Get information about a specific group.
