# Data Functions

Detailed argument specifications, output schemas, and usage guidance for
`get_data`, `get_data_by_countries`, and `get_all_countries_data`.

## 1. `get_data` — Time series for one country

Returns yearly time series data for a single country and indicator.

```bash
uv run scripts/world_bank_api.py ./data.json get_data US NY.GDP.MKTP.CD --start 2010 --end 2020
uv run scripts/world_bank_api.py ./data.json get_data WLD SP.POP.TOTL --start 2000
uv run scripts/world_bank_api.py ./data.json get_data GBR NY.GDP.PCAP.CD
```

**Arguments:**

-   `country_code` (str, required) — ISO country code (e.g. `"US"`, `"GBR"`,
    `"WLD"` for world aggregate).
-   `indicator_id` (str, required) — Indicator code (e.g.
    `"NY.GDP.MKTP.CD"`).
-   `start` (str, default `""`) — Start year (e.g. `"2010"`). Empty string for
    no lower bound (defaults to 1960).
-   `end` (str, default `""`) — End year (e.g. `"2020"`). Empty string for
    most recent available data.

**Output:** `list[object]` — one object per year, with:

-   `indicator` (object) — `{id, value}` — indicator ID and name
-   `country` (object) — `{id, value}` — country ISO code and name
-   `countryiso3code` (string) — ISO alpha-3 code
-   `date` (string) — Year (e.g. `"2020"`)
-   `value` (string | null) — Indicator value as a string. Null when data is
    not available for that year.
-   `unit` (string) — Unit of measurement
-   `obs_status` (string) — Observation status code
-   `decimal` (integer) — Number of decimal places

**Important:** The `value` field is a **string** and may be `null` for years
where data is missing. Use `tonumber` in `jq` to convert to numeric for sorting
or arithmetic:

```bash
cat ./data.json | jq '[.[] | select(.value != null) | {year: .date, gdp: (.value | tonumber)}] | sort_by(.date)'
```

**Date filtering behavior:**
-   If only `start` is set (e.g. `--start 2010`): data from 2010 onward.
-   If only `end` is set (e.g. `--end 2020`): data from 1960 to 2020.
-   If both are set: data in the range `start:end`.
-   If neither is set (default): all available years (typically 1960 to
    present). Limited to 100 results; use a date range to get more.

--------------------------------------------------------------------------------

## 2. `get_data_by_countries` — Multi-country time series

Returns time series data for multiple countries and one indicator.

```bash
uv run scripts/world_bank_api.py ./multi.json get_data_by_countries "US,GBR,DEU,FRA" NY.GDP.MKTP.CD --start 2010 --end 2020
uv run scripts/world_bank_api.py ./multi_pop.json get_data_by_countries "CHN,IND,USA" SP.POP.TOTL --start 2000 --end 2020
```

**Arguments:**

-   `countries` (list[str], required) — Comma-separated list of ISO country
    codes (e.g. `"US,GBR,DEU"`).
-   `indicator_id` (str, required) — Indicator code.
-   `start` (str, default `""`) — Start year.
-   `end` (str, default `""`) — End year.

**Output:** `list[object]` — same schema as `get_data`, concatenated across all
countries.

**Filtering by country after retrieval:**

```bash
cat ./multi.json | jq '[.[] | select(.country.id == "US") | {year: .date, value: .value}]'
```

**Note on large requests:** The World Bank API can handle up to around 50
country codes at once (joined with `;` in the URL). For very large country
lists, consider using `get_all_countries_data` instead.

--------------------------------------------------------------------------------

## 3. `get_all_countries_data` — All countries, one indicator, one year

Returns data for ALL available countries for a single indicator in a specific
year. Ideal for cross-country comparisons, rankings, and maps.

```bash
uv run scripts/world_bank_api.py ./gdp_2020.json get_all_countries_data NY.GDP.MKTP.CD 2020
uv run scripts/world_bank_api.py ./life_exp.json get_all_countries_data SP.DYN.LE00.IN 2019
```

**Arguments:**

-   `indicator_id` (str, required) — Indicator code.
-   `year` (str, required) — Year to retrieve data for (e.g. `"2020"`,
    `"2019"`).

**Output:** `list[object]` — same schema as `get_data`, with one entry per
country that has data for that year.

**Common usage patterns:**

**Top 10 countries by GDP in 2020:**

```bash
cat ./gdp_2020.json | jq '[.[] | select(.value != null) | {country: .country.value, gdp: (.value | tonumber)}] | sort_by(.gdp) | reverse[:10]'
```

**Countries with no data (null values):**

```bash
cat ./gdp_2020.json | jq '[.[] | select(.value == null) | .country.value]'
```

**Count of countries with available data:**

```bash
cat ./gdp_2020.json | jq '[.[] | select(.value != null)] | length'
```

**Limitations:**
-   The endpoint returns at most 500 results per call. For indicators with data
    in ~200+ countries, this should be sufficient.
-   Only one year at a time. For multi-year, multi-country data, use
    `get_data_by_countries` with a date range.
-   Regional aggregates (EUU, ECS) appear as separate entries alongside
    individual countries.
