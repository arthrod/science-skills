# Dockets & Cases Functions

Detailed argument specifications, output schemas, and usage guidance for
`search_dockets`, `get_docket_entries`, and `get_docket_by_case_number`.

## 1. `search_dockets` — Search dockets by case name

Returns a list of docket records matching a free-text query. Dockets are
the official case records maintained by courts.

```bash
uv run scripts/courtlistener_api.py ./dockets.json search_dockets "Marbury v. Madison" --court scotus --limit 5
uv run scripts/courtlistener_api.py ./dockets.json search_dockets "civil rights" --limit 10
```

**Arguments:**

-   `query` (str, required) — free-text search query (searches case name/title)
-   `court` (str, default "") — court ID abbreviation (e.g. `ca1`, `scotus`).
    Empty string searches all courts.
-   `limit` (int, default 10) — maximum number of dockets to return

**Output:** `list[object]` — one object per docket:

-   `id` (int) — CourtListener docket ID
-   `absolute_url` (str) — URL path on courtlistener.com
-   `caseName` (str) — full case name
-   `court` (str) — court ID abbreviation
-   `court_citation_string` (str) — human-readable court name
-   `court_id` (str) — court resource URL
-   `dateArgued` (str | null) — date argued in `YYYY-MM-DD` format
-   `dateFiled` (str | null) — date filed in `YYYY-MM-DD` format
-   `dateTerminated` (str | null) — date terminated/closed
-   `docketNumber` (str | null) — docket/case number
-   `type` (str) — result type (always `"docket"`)
-   `snippet` (str | null) — highlighted text excerpt (may be empty)

---

## 2. `get_docket_entries` — Get entries for a docket

Retrieves the docket entries (individual filings, orders, and events) for a
specific docket. Each entry represents a document filed or action taken in
the case.

```bash
uv run scripts/courtlistener_api.py ./entries.json get_docket_entries 98765 --limit 20
```

**Arguments:**

-   `docket_id` (int, required) — numeric ID of the docket
-   `limit` (int, default 50) — maximum number of entries to return

**Output:** `list[object]` — one object per docket entry:

-   `id` (int) — entry ID
-   `date_created` (str) — ISO-8601 timestamp
-   `date_modified` (str) — ISO-8601 timestamp of last modification
-   `date_filed` (str | null) — date the entry was filed in `YYYY-MM-DD`
    format
-   `description` (str | null) — text description of the entry
-   `docket` (str) — API URL to the parent docket
-   `pacer_doc_id` (str | null) — PACER document ID if available
-   `pacer_seq_no` (int | null) — PACER sequence number
-   `document_number` (str | null) — document number in the docket
-   `entry_number` (int | null) — entry number in chronological order

**Important**: Docket entries from federal courts may include `pacer_doc_id`
and `document_number` fields that can be used to retrieve documents from
PACER. State court entries may have fewer fields populated.

---

## 3. `get_docket_by_case_number` — Lookup by case number

Looks up a docket by its case number within a specific court. This is useful
when you know the exact case number (e.g. from a citation or PACER query).

```bash
uv run scripts/courtlistener_api.py ./docket.json get_docket_by_case_number "20-1234" ca1
```

**Arguments:**

-   `case_number` (str, required) — case number string (e.g. `"20-1234"`,
    `"1:20-cv-01234"`)
-   `court` (str, required) — court ID abbreviation (e.g. `ca1`, `dcd`)

**Output:** `object` — the first matching docket object:

-   `id` (int) — docket ID
-   `date_created` (str) — ISO-8601 timestamp
-   `date_modified` (str) — ISO-8601 timestamp of last modification
-   `dateArgued` (str | null) — date argued in `YYYY-MM-DD` format
-   `dateFiled` (str | null) — date filed in `YYYY-MM-DD` format
-   `dateTerminated` (str | null) — date terminated/closed
-   `case_name` (str) — full case name
-   `case_name_short` (str | null) — abbreviated case name
-   `docket_number` (str | null) — docket/case number
-   `court` (str) — API URL to the court resource

**On error**: Returns `{"error": "No docket found for this case number and
court"}` if no matching docket exists.
