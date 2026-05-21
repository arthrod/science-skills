# Data Functions

Detailed argument specifications, output schemas, and usage guidance for
`get_series_observations`, `get_series_categories`, `get_series_release`,
and `get_series_tags`.

## 1. `get_series_observations` — Time series values

Retrieves the actual data values (observations) for a FRED series. This is
the primary function for getting economic data.

```bash
uv run scripts/fred_api.py ./gdp_data.json get_series_observations "GDP" --start "2019-01-01" --end "2023-12-31"
uv run scripts/fred_api.py ./unrate_data.json get_series_observations "UNRATE" --frequency "m"
```

**Arguments:**

- `series_id` (str, required) — FRED series ID
- `start` (str, optional) — Start date in `"YYYY-MM-DD"` format. If omitted,
  returns all observations from the earliest available date.
- `end` (str, optional) — End date in `"YYYY-MM-DD"` format. If omitted,
  returns all observations up to the latest available date.
- `frequency` (str, optional) — Frequency aggregation. One of:
  - `"d"` — Daily
  - `"w"` — Weekly
  - `"bw"` — Biweekly
  - `"m"` — Monthly
  - `"q"` — Quarterly
  - `"sa"` — Semiannual
  - `"a"` — Annual

**Output:** `object` — top-level keys:

| Key | Type | Description |
|-----|------|-------------|
| `realtime_start` | string | Real-time period start |
| `realtime_end` | string | Real-time period end |
| `observation_start` | string | Earliest observation in response |
| `observation_end` | string | Latest observation in response |
| `units` | string | Units (inherited from series) |
| `output_type` | int | Output type code |
| `file_type` | string | Always `"json"` |
| `order_by` | string | Sort order |
| `sort_order` | string | Ascending or descending |
| `count` | int | Number of observations |
| `observations` | list | Array of observation objects |

Each observation object:

| Key | Type | Description |
|-----|------|-------------|
| `realtime_start` | string | Real-time period start |
| `realtime_end` | string | Real-time period end |
| `date` | string | Observation date (`"YYYY-MM-DD"`) |
| `value` | string | Observation value (string, may be `"."` for missing) |

**Important**: The `value` field is a string, not a number. Missing or
suppressed values are represented as `"."`. Use `jq` to convert:
```bash
cat ./data.json | jq '[.observations[] | select(.value != ".") | {date, value: (.value | tonumber)}]'
```

**Date filtering**: If both `start` and `end` are omitted, the API returns
all available observations, which may be a very large dataset. Always
specify a date range when possible.

---

## 2. `get_series_categories` — Categories for a series

Returns the FRED categories that a series belongs to.

```bash
uv run scripts/fred_api.py ./gdp_categories.json get_series_categories "GDP"
```

**Arguments:**

- `series_id` (str, required) — FRED series ID

**Output:** `list[object]` — each with:

| Key | Type | Description |
|-----|------|-------------|
| `id` | int | Category ID |
| `name` | string | Category name |
| `parent_id` | int | Parent category ID |

---

## 3. `get_series_release` — Release for a series

Returns the economic release that a series belongs to.

```bash
uv run scripts/fred_api.py ./gdp_release.json get_series_release "GDP"
```

**Arguments:**

- `series_id` (str, required) — FRED series ID

**Output:** `object` — with:

| Key | Type | Description |
|-----|------|-------------|
| `id` | int | Release ID |
| `realtime_start` | string | Real-time start |
| `realtime_end` | string | Real-time end |
| `name` | string | Release name (e.g. `"Gross Domestic Product"`) |
| `press_release` | string | Whether a press release exists |
| `link` | string | Link to release info |
| `notes` | string | Release notes |

---

## 4. `get_series_tags` — Tags for a series

Returns the FRED tags associated with a series.

```bash
uv run scripts/fred_api.py ./gdp_tags.json get_series_tags "GDP"
```

**Arguments:**

- `series_id` (str, required) — FRED series ID

**Output:** `list[object]` — each with:

| Key | Type | Description |
|-----|------|-------------|
| `name` | string | Tag name (e.g. `"gdp"`, `"usa"`) |
| `group_id` | string | Tag group (e.g. `"geo"`, `"freq"`, `"gen"`) |
| `notes` | string | Tag description / notes |
| `created` | string | When the tag was created |
| `popularity` | int | Tag popularity score |
| `series_count` | int | Number of series with this tag |
