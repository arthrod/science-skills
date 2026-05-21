# Search Opinions Functions

Detailed argument specifications, output schemas, and usage guidance for
`search_opinions`, `get_opinion_by_id`, and `get_opinion_citations`.

## 1. `search_opinions` — Search full-text court opinions

Returns a list of opinions matching a free-text query across the CourtListener
database. Supports filters by court and filing date range.

```bash
uv run scripts/courtlistener_api.py ./search_results.json search_opinions "fourth amendment" --court scotus --limit 5
uv run scripts/courtlistener_api.py ./opinions.json search_opinions "negligence" --filed_after 2020-01-01 --filed_before 2023-12-31 --limit 10
```

**Arguments:**

-   `query` (str, required) — free-text search query
-   `court` (str, default "") — court ID abbreviation (e.g. `ca1`, `ca9`,
    `scotus`). Empty string searches all courts.
-   `filed_after` (str, default "") — date string in `YYYY-MM-DD` format.
    Filters results filed on or after this date.
-   `filed_before` (str, default "") — date string in `YYYY-MM-DD` format.
    Filters results filed on or before this date.
-   `limit` (int, default 10) — maximum number of opinions to return

**Output:** `list[object]` — one object per opinion:

-   `id` (int) — CourtListener opinion ID
-   `absolute_url` (str) — URL path on courtlistener.com
-   `caseName` (str) — full case name (e.g. `"Brown v. Board of Education"`)
-   `cite` (str) — standardized citation string
-   `court` (str) — court ID abbreviation
-   `court_citation_string` (str) — human-readable court name
-   `dateFiled` (str | null) — filing date in `YYYY-MM-DD` format
-   `dateArgued` (str | null) — argument date if applicable
-   `court_id` (str) — court resource ID
-   `docket` (str) — URL to the docket resource
-   `cluster` (str) — URL to the opinion cluster
-   `snippet` (str) — highlighted text excerpt (may be empty)
-   `type` (str) — result type (always `"opinion"` for this search)
-   `status` (str) — precedential status (e.g. `"Published"`, `"Unpublished"`)

**Filtering tips:**

-   **By court**: Knowing the court ID is essential for targeted searches.
    Use `list_courts` (or reference [courts-judges.md](courts-judges.md)) to
    find court IDs. Common ones: `scotus` (Supreme Court), `ca1`–`ca11`
    (Circuit Courts), `dcd` (D.C. District).
-   **By date**: Use `filed_after` and `filed_before` with `YYYY-MM-DD`
    format. Combining both gives a date range.
-   **By precedential status**: Filter post-query with `jq`, e.g.:
    ```bash
    cat ./search_results.json | jq '[.[] | select(.status == "Published")]'
    ```

**Common court IDs:**

| Court ID | Description |
|----------|-------------|
| scotus | Supreme Court of the United States |
| ca1–ca11 | U.S. Courts of Appeals (1st–11th Circuits) |
| cadc | D.C. Circuit Court of Appeals |
| cafc | Federal Circuit Court of Appeals |
| dcd | D.C. District Court |
| *state-abbrev* | State supreme courts (e.g. `cal` for California Supreme Court) |

---

## 2. `get_opinion_by_id` — Get a specific opinion

Retrieves full metadata for a single opinion by its numeric CourtListener
opinion ID.

```bash
uv run scripts/courtlistener_api.py ./opinion.json get_opinion_by_id 123456
```

**Arguments:**

-   `opinion_id` (int, required) — numeric ID of the opinion

**Output:** `object` — full opinion object with these key fields:

-   `id` (int) — opinion ID
-   `date_created` (str) — ISO-8601 timestamp of when the opinion was added
-   `date_modified` (str) — ISO-8601 timestamp of last modification
-   `author` (int | null) — ID of the authoring judge, or null
-   `per_curiam` (bool) — whether the opinion is per curiam
-   `joined_by` (list[int]) — IDs of judges joining the opinion
-   `type` (str) — opinion type (e.g. `"010combined"`, `"020lead"`,
    `"030concurrence"`, `"040dissent"`)
-   `download_url` (str | null) — URL to download the opinion file
-   `local_path` (str | null) — local path if downloaded
-   `plain_text` (str | null) — full plain text of the opinion
-   `html` (str | null) — HTML version of the opinion
-   `html_anon_2020` (str | null) — anonymized HTML version
-   `html_columbia` (str | null) — Columbia-specific HTML version
-   `html_with_citations` (str | null) — HTML with citation links
-   `page_count` (int | null) — number of pages
-   `sha1` (str) — SHA-1 hash of the opinion file
-   `cluster_id` (int) — ID of the opinion cluster (grouping of related
    opinions for the same case)

**Important**: The `plain_text` field can be very large for long opinions.
Use judiciously with `jq` to extract summaries or head/tail to sample.

---

## 3. `get_opinion_citations` — Get citations for an opinion

Returns citations to and from a specific opinion. This endpoint surfaces
both citing and cited opinions linked to the given opinion.

```bash
uv run scripts/courtlistener_api.py ./citations.json get_opinion_citations 123456
```

**Arguments:**

-   `opinion_id` (int, required) — numeric ID of the opinion

**Output:** `list[object]` — list of citation objects:

-   `id` (int) — citation record ID
-   `volume` (str) — reporter volume number
-   `reporter` (str) — reporter abbreviation
-   `page` (str) — starting page
-   `type` (int) — citation type (1 = federal, 2 = state, etc.)
-   `opinion_id` (int) — the opinion this citation belongs to
-   `cluster_id` (int) — the opinion cluster
