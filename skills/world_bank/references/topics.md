# Topics & Bulk Functions

Detailed argument specifications, output schemas, and usage guidance for
`list_topics`, `get_topic`, and `get_country_indicators`.

## 1. `list_topics` — List development topics

Returns all available development topics. Topics are used to categorize and
filter indicators.

```bash
uv run scripts/world_bank_api.py ./topics.json list_topics
uv run scripts/world_bank_api.py ./topics.json list_topics --limit 20
```

**Arguments:**

-   `limit` (int, default 50) — Maximum topics to return.

**Output:** `list[object]` — each object contains:

-   `id` (string) — Numeric topic ID
-   `value` (string) — Topic name

**Common topic IDs:**

| ID | Topic |
|---|-------|
| 1 | Economic Policy & Debt |
| 2 | Environment |
| 3 | Financial Sector |
| 4 | Health |
| 5 | Infrastructure |
| 6 | Poverty |
| 7 | Private Sector |
| 8 | Public Sector |
| 9 | Social Protection & Labor |
| 10 | Trade |
| 11 | Urban Development |
| 12 | Gender |
| 13 | Science & Technology |
| 14 | Climate Change |
| 15 | Agriculture & Rural Development |
| 16 | Education |
| 17 | Energy & Mining |
| 18 | External Debt |
| 19 | Aid Effectiveness |
| 20 | Public & Private Sector Partnerships |

**Usage with `search_indicators`:** Pass a topic ID to narrow indicator
searches. For example:

```bash
# Search for health indicators only
uv run scripts/world_bank_api.py ./health_indicators.json search_indicators "mortality" --topic 4
```

--------------------------------------------------------------------------------

## 2. `get_topic` — Get topic details

Returns details for a single development topic by its numeric ID.

```bash
uv run scripts/world_bank_api.py ./topic.json get_topic 4
uv run scripts/world_bank_api.py ./topic.json get_topic 1
```

**Arguments:**

-   `topic_id` (int, required) — Numeric topic ID (e.g. `4` for Health, `1`
    for Economic Policy & Debt).

**Output:** `list[object]` — one object with:

-   `id` (string) — Numeric topic ID
-   `value` (string) — Topic name
-   `sourceNote` (string) — Description and notes about the topic

**Empty topic IDs:** The topics with IDs outside the 1-20 range may return
empty results. If a topic ID returns an empty list `[]`, it means the topic
does not exist or has no associated data.

**Chaining pattern — explore topics, then filter indicators:**

```bash
# 1. List all topics
uv run scripts/world_bank_api.py ./topics.json list_topics --limit 50

# 2. Get details about topic 4 (Health)
uv run scripts/world_bank_api.py ./health_topic.json get_topic 4
cat ./health_topic.json | jq '.[].sourceNote'

# 3. Search indicators within that topic
uv run scripts/world_bank_api.py ./health_indicators.json search_indicators "immunization" --topic 4
```

--------------------------------------------------------------------------------

## 3. `get_country_indicators` — List indicators for a country

Returns all available indicators for a specific country. Useful for discovering
which datasets exist for a country of interest.

```bash
uv run scripts/world_bank_api.py ./us_indicators.json get_country_indicators US --limit 20
uv run scripts/world_bank_api.py ./rwanda_indicators.json get_country_indicators RWA
```

**Arguments:**

-   `country_code` (str, required) — ISO country code (e.g. `"US"`, `"RWA"`,
    `"CHN"`).
-   `limit` (int, default 50) — Maximum indicators to return.

**Output:** `list[object]` — each object contains indicator metadata with the
same schema as `get_indicator` output:

-   `id` (string) — Indicator code
-   `name` (string) — Full indicator name
-   `unit` (string) — Unit of measurement
-   `source` (object) — `{id, value}` — source organization
-   `sourceNote` (string) — Description
-   `sourceOrganization` (string) — Organization name
-   `topics` (list[object]) — `[{id, value}]` — associated topics

**Note:** This endpoint returns indicators that *have ever had* data for the
country, not just currently populated indicators. Some indicators may return
null values for specific years.

**Finding what data exists for a country:**

```bash
# 1. Get all indicators for a country (may be a large list)
uv run scripts/world_bank_api.py ./ke_indicators.json get_country_indicators KEN --limit 200

# 2. Filter to health-related indicators
cat ./ke_indicators.json | jq '[.[] | select(.topics[]?.value == "Health") | {id, name}]'

# 3. Pick an indicator and get data
uv run scripts/world_bank_api.py ./ke_health_data.json get_data KEN SH.XPD.CHEX.GD.ZS --start 2000 --end 2020
```

**Limitations:**
-   The endpoint may return a very large number of results (thousands of
    indicators). Always use `--limit` to constrain the output.
-   Country-specific indicator availability varies. A country with limited
    statistical capacity may have far fewer indicators available.
