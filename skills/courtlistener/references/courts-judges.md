# Courts & Judges Functions

Detailed argument specifications, output schemas, and usage guidance for
`list_courts`, `search_judges`, and `get_judge_opinions`.

## 1. `list_courts` — List all available courts

Returns a complete list of all courts in the CourtListener database, including
federal, state, territorial, and tribal courts.

```bash
uv run scripts/courtlistener_api.py ./courts.json list_courts
cat ./courts.json | jq '.[] | {id: .id, full_name: .full_name}' -r
```

**Arguments:** None.

**Output:** `list[object]` — one object per court:

-   `id` (str) — court ID abbreviation (e.g. `"scotus"`, `"ca1"`, `"cal"`)
-   `date_created` (str) — ISO-8601 timestamp
-   `date_modified` (str) — ISO-8601 timestamp of last modification
-   `slug` (str) — URL-friendly version of the court name
-   `in_use` (bool) — whether the court is currently active
-   `full_name` (str) — full official name (e.g. `"Supreme Court of the
    United States"`)
-   `short_name` (str) — abbreviated name (e.g. `"S. Ct."`)
-   `citation_string` (str | null) — citation abbreviation for the court's
    reporter (e.g. `"U.S."` for SCOTUS)
-   `url` (str | null) — official court website URL
-   `start_date` (str | null) — date the court came into existence
-   `end_date` (str | null) — date the court ceased to exist (null if current)
-   `jurisdiction` (str) — jurisdiction type (e.g. `"F"` for federal,
    `"S"` for state, `"T"` for territorial, `"FB"` for federal bankruptcy)
-   `jurisdiction_type` (str | null) — more specific type (e.g.
    `"Supreme Court"`, `"Appeals"`, `"District"`, `"Bankruptcy"`)
-   `notes` (str | null) — additional notes about the court

**Filtering by jurisdiction:**

```bash
# List only federal courts
cat ./courts.json | jq '[.[] | select(.jurisdiction == "F")]'

# List only state supreme courts
cat ./courts.json | jq '[.[] | select(.id | test("^[a-z]{2,2}$"))]'
```

---

## 2. `search_judges` — Search judges

Searches for judges and other legal professionals (people) in the
CourtListener database. Results can be filtered by name and court.

```bash
uv run scripts/courtlistener_api.py ./judges.json search_judges --name "Ginsburg"
uv run scripts/courtlistener_api.py ./judges.json search_judges --court scotus
uv run scripts/courtlistener_api.py ./judges.json search_judges --name "Roberts" --court scotus
```

**Arguments:**

-   `name` (str, default "") — judge name to search for (partial match
    supported)
-   `court` (str, default "") — court ID abbreviation to filter by (e.g.
    `scotus`, `ca9`)

**Output:** `list[object]` — one object per person/judge:

-   `id` (int) — person ID (used for `get_judge_opinions`)
-   `date_created` (str) — ISO-8601 timestamp
-   `date_modified` (str) — ISO-8601 timestamp
-   `name` (str) — full name of the person
-   `name_full` (str) — full formatted name
-   `name_reverse` (str) — name in `"LastName, FirstName"` format
-   `name_slug` (str) — URL-friendly name
-   `gender` (str | null) — gender if known
-   `dob` (str | null) — date of birth in `YYYY-MM-DD` format
-   `dob_city` (str | null) — city of birth
-   `dob_state` (str | null) — state of birth
-   `dod` (str | null) — date of death in `YYYY-MM-DD` format
-   `political_affiliation` (str | null) — political affiliation if known
    (e.g. `"d"` for Democrat, `"r"` for Republican)
-   `races` (list[str]) — racial/ethnic identities
-   `school` (list[str]) — law schools attended
-   `court` (str) — API URL to the court the judge is associated with
-   `date_start` (str | null) — date assumed office
-   `date_retirement` (str | null) — date of retirement
-   `date_termination` (str | null) — date of termination
-   `appointer` (str | null) — who appointed the judge
-   `supervision` (str | null) — supervising judge if applicable
-   `fjc_id` (int | null) — Federal Judicial Center ID

**Important**: The `id` field from the results is the `person_id` you need
for `get_judge_opinions`.

---

## 3. `get_judge_opinions` — Opinions by a specific judge

Returns opinions authored by a specific judge (identified by their CourtListener
person ID).

```bash
# First, find a judge's ID
uv run scripts/courtlistener_api.py ./ginsburg.json search_judges --name "Ginsburg" --court scotus
JUDGE_ID=$(cat ./ginsburg.json | jq '.[0].id')

# Then get their opinions
uv run scripts/courtlistener_api.py ./ginsburg_opinions.json get_judge_opinions "$JUDGE_ID" --limit 20
```

**Arguments:**

-   `person_id` (int, required) — numeric ID of the judge/person
-   `limit` (int, default 50) — maximum number of opinions to return

**Output:** `list[object]` — list of opinion objects (same schema as
`get_opinion_by_id` results but limited to opinions authored by this judge):

-   `id` (int) — opinion ID
-   `date_created` (str) — ISO-8601 timestamp
-   `date_modified` (str) — ISO-8601 timestamp
-   `author` (int) — person ID of the author (matches the input person_id)
-   `per_curiam` (bool) — per curiam flag
-   `joined_by` (list[int]) — list of person IDs of joining judges
-   `type` (str) — opinion type
-   `download_url` (str | null) — URL to download the opinion
-   `plain_text` (str | null) — full plain text of the opinion
-   `cluster_id` (int) — opinion cluster ID

**Key fields for analysis:**

-   `type`: Identifies the opinion role:
    -   `"010combined"` — combined/single opinion
    -   `"020lead"` — lead opinion (plurality)
    -   `"030concurrence"` — concurring opinion
    -   `"040dissent"` — dissenting opinion
-   `plain_text`: The full text of the opinion. Can be very long; use
    `jq -r '.plain_text' | head -N` to sample.
-   `cluster_id`: Use this to find related opinions in the same case by
    looking up opinions with the same cluster.
