# Oral Arguments Functions

Detailed argument specifications, output schemas, and usage guidance for
`search_oral_arguments` and `get_oral_argument`.

## 1. `search_oral_arguments` — Search oral argument recordings

Searches for oral argument recordings in the CourtListener database. Returns
metadata and download URLs for audio recordings of court proceedings.

```bash
uv run scripts/courtlistener_api.py ./oral_args.json search_oral_arguments "free speech" --court scotus --limit 5
uv run scripts/courtlistener_api.py ./oral_args.json search_oral_arguments "Miranda" --date_after 2010-01-01 --limit 10
```

**Arguments:**

-   `query` (str, required) — free-text search query for case name/issue
-   `court` (str, default "") — court ID abbreviation (e.g. `scotus`).
    Empty string searches all courts.
-   `date_after` (str, default "") — date string in `YYYY-MM-DD` format.
    Filters arguments heard on or after this date.
-   `limit` (int, default 10) — maximum number of results to return

**Output:** `list[object]` — one object per oral argument:

-   `id` (int) — oral argument ID
-   `absolute_url` (str) — URL path on courtlistener.com
-   `caseName` (str) — full case name
-   `court` (str) — court ID abbreviation
-   `court_citation_string` (str) — human-readable court name
-   `court_id` (str) — API URL to the court resource
-   `dateArgued` (str | null) — date argued in `YYYY-MM-DD` format
-   `docket` (str) — API URL to the associated docket
-   `type` (str) — result type (always `"oral_argument"`)
-   `snippet` (str | null) — highlighted text excerpt (may be empty)

**Important**: The download URL for the audio file is obtained by calling
`get_oral_argument` with the oral argument `id`.

---

## 2. `get_oral_argument` — Get oral argument metadata

Retrieves full metadata and download URL for a specific oral argument
recording by its numeric ID.

```bash
# First, find an oral argument ID
uv run scripts/courtlistener_api.py ./oa_search.json search_oral_arguments "Miranda" --court scotus --limit 1
OA_ID=$(cat ./oa_search.json | jq '.[0].id')

# Then get full details including download URL
uv run scripts/courtlistener_api.py ./oa_detail.json get_oral_argument "$OA_ID"
```

**Arguments:**

-   `oa_id` (int, required) — numeric ID of the oral argument

**Output:** `object` — full oral argument object with key fields:

-   `id` (int) — oral argument ID
-   `date_created` (str) — ISO-8601 timestamp
-   `date_modified` (str) — ISO-8601 timestamp
-   `dateArgued` (str | null) — date argued in `YYYY-MM-DD` format
-   `duration` (int | null) — duration in seconds
-   `caseName` (str) — full case name
-   `court` (str) — API URL to the court
-   `court_id` (str) — court ID abbreviation
-   `docket` (str) — API URL to the docket
-   `download_url` (str | null) — URL to download the audio file (MP3)
-   `local_path_mp3` (str | null) — local path to downloaded MP3
-   `local_path_original_file` (str | null) — local path to original file

**Key fields for retrieval:**

-   `download_url`: Use this to download the MP3 audio recording.
    The audio files are typically in MP3 format.
-   `duration`: Duration in seconds. Convert to minutes:
    ```bash
    echo "scale=2; $(cat ./oa_detail.json | jq '.duration') / 60" | bc
    ```

**Example download workflow:**

```bash
# Get download URL
DOWNLOAD_URL=$(cat ./oa_detail.json | jq -r '.download_url // empty')
if [ -n "$DOWNLOAD_URL" ]; then
  curl -o argument.mp3 "$DOWNLOAD_URL"
  echo "Downloaded oral argument to argument.mp3"
fi
```

**Note on usage**: Oral argument audio files are typically large (30–90
minutes of audio = 10–50 MB). Only download when the user explicitly requests
the audio content. For metadata-only queries, `search_oral_arguments` is
sufficient.
