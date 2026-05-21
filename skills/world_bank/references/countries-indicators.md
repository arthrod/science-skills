# Countries & Indicators Functions

Detailed argument specifications, output schemas, and usage guidance for
`get_country`, `search_countries`, `search_indicators`, and `get_indicator`.

## 1. `get_country` — Get country metadata

Returns metadata for a single country by its ISO code.

```bash
uv run scripts/world_bank_api.py ./country.json get_country US
```

**Arguments:**

-   `country_code` (str, required) — ISO 3166-1 alpha-2, alpha-3, or numeric
    country code. Examples: `"US"`, `"GBR"`, `"FRA"`, `"076"`.

**Output:** `list[object]` — one object with country fields:

| Field | Type | Description |
|---|---|---|
| `id` | string | ISO alpha-2 code |
| `iso2Code` | string | ISO alpha-2 code |
| `name` | string | Country name |
| `region` | object | `{id, value}` — e.g. `"North America"` |
| `adminregion` | object | `{id, value}` — administrative region |
| `incomeLevel` | object | `{id, value}` — e.g. `"High income"` |
| `lendingType` | object | `{id, value}` — e.g. `"IBRD"` |
| `capitalCity` | string | Capital city name |
| `longitude` | string | Longitude |
| `latitude` | string | Latitude |

(Since the reference file is markdown and Telegram has no tables, the field
list above uses pipe-table syntax which is only valid in the markdown source.
The actual output is a JSON object.)

**Common country codes:**
-   `WLD` — World (aggregate)
-   `ECS` — All economies (aggregate)
-   `EUU` — European Union
-   `US`, `GBR`, `FRA`, `DEU`, `CHN`, `JPN`, `IND`, `BRA`, `CAN`, `AUS`

Code lookups are case-insensitive on alpha-2 codes.

--------------------------------------------------------------------------------

## 2. `search_countries` — Search countries by name

Searches the World Bank country database by partial name match.

```bash
uv run scripts/world_bank_api.py ./countries.json search_countries "Germany"
uv run scripts/world_bank_api.py ./countries.json search_countries "United" --limit 10
```

**Arguments:**

-   `query` (str, required) — Partial or full country name to search for.
-   `limit` (int, default 50) — Maximum results to return.

**Output:** `list[object]` — each object follows the same schema as
`get_country`. Returns an empty list if no matches found.

**Troubleshooting:**
-   Try both short and full official names (e.g. "US" vs "United States",
    "Russia" vs "Russian Federation").
-   The search endpoint matches on name only, not on ISO code. Use
    `get_country` for exact code lookups.
-   Region and income aggregates (WLD, EUU, ECS) are not returned by this
    search; use `get_country` with the aggregate code instead.

--------------------------------------------------------------------------------

## 3. `search_indicators` — Search available indicators

Finds indicators by keyword matching against their name and description.

```bash
uv run scripts/world_bank_api.py ./indicators.json search_indicators "GDP"
uv run scripts/world_bank_api.py ./indicators.json search_indicators "population" --topic 4 --limit 20
```

**Arguments:**

-   `query` (str, required) — Keyword to search for in indicator names and
    descriptions.
-   `topic` (int, default 0) — Topic ID to narrow results. Pass `0` or omit
    for no topic filter. See `list_topics` for available topic IDs.
-   `limit` (int, default 50) — Maximum results to return.

**Output:** `list[object]` — each object contains:

-   `id` (string) — Indicator code (e.g. `"NY.GDP.MKTP.CD"`)
-   `name` (string) — Human-readable indicator name
-   `unit` (string) — Measurement unit
-   `source` (object) — `{id, value}` — data source
-   `sourceNote` (string) — Description of the indicator

**Common indicator IDs:**

| Code | Name |
|---|---|
| `NY.GDP.MKTP.CD` | GDP (current US$) |
| `NY.GDP.PCAP.CD` | GDP per capita (current US$) |
| `NY.GDP.MKTP.KD.ZG` | GDP growth (annual %) |
| `SP.POP.TOTL` | Population, total |
| `SP.POP.GROW` | Population growth (annual %) |
| `SP.DYN.LE00.IN` | Life expectancy at birth (years) |
| `SE.PRM.ENRR` | School enrollment, primary (% gross) |
| `SH.XPD.CHEX.GD.ZS` | Current health expenditure (% of GDP) |
| `EN.ATM.CO2E.KT` | CO2 emissions (kt) |
| `SL.UEM.TOTL.ZS` | Unemployment (% of total labor force) |
| `FP.CPI.TOTL.ZG` | Consumer price index (annual %) |
| `BX.KLT.DINV.WD.GD.ZS` | Foreign direct investment (% of GDP) |

**Pro tip:** Indicator IDs are case-sensitive and use dot notation.
Searching for partial matches on the ID (e.g. `GDP`) in the query is the most
reliable way to find the right indicator. Common prefixes:

-   `NY.` — National accounts (GDP, GNI)
-   `SP.` — Population & demographics
-   `SH.` — Health
-   `SE.` — Education
-   `EN.` — Environment
-   `SL.` — Labor & social protection
-   `FP.` — Financial sector
-   `BX.`, `BM.` — Balance of payments
-   `AG.` — Agriculture
-   `EG.` — Energy

--------------------------------------------------------------------------------

## 4. `get_indicator` — Get indicator metadata

Returns detailed metadata for a single indicator by its ID.

```bash
uv run scripts/world_bank_api.py ./indicator.json get_indicator NY.GDP.MKTP.CD
```

**Arguments:**

-   `indicator_id` (str, required) — Indicator code (e.g.
    `"NY.GDP.MKTP.CD"`, `"SP.POP.TOTL"`).

**Output:** `list[object]` — one object with:

-   `id` (string) — Indicator code
-   `name` (string) — Full indicator name
-   `unit` (string) — Unit of measurement
-   `source` (object) — `{id, value}` — source organization
-   `sourceNote` (string) — Description
-   `sourceOrganization` (string) — Organization name
-   `topics` (list[object]) — `[{id, value}]` — associated topics
