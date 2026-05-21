# Search Functions

Detailed argument specifications, output schemas, search strategies, and
troubleshooting for `search_series` and `get_series_info`.

## 1. `search_series` — Find economic series

Searches FRED for economic series matching a free-text query. Supports both
full-text search (default) and series ID search.

```bash
uv run scripts/fred_api.py ./search_results.json search_series "Gross Domestic Product" --search_type full_text --limit 5
uv run scripts/fred_api.py ./search_results.json search_series "GDP" --search_type series_id
```

**Arguments:**

- `query` (str, required) — Free-text search string or series ID pattern
- `search_type` (str, default `"full_text"`) — Either `"full_text"` or
  `"series_id"`
- `limit` (int, default 25) — Maximum number of series to return (max 1000)

**Output:** `list[object]` — each object contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | FRED series ID (e.g. `"GDP"`) |
| `realtime_start` | string | Real-time period start |
| `realtime_end` | string | Real-time period end |
| `title` | string | Human-readable title |
| `observation_start` | string | Earliest observation date |
| `observation_end` | string | Latest observation date |
| `frequency` | string | Data frequency (e.g. `"Quarterly"`) |
| `frequency_short` | string | Short frequency code (e.g. `"Q"`) |
| `units` | string | Units of measurement |
| `units_short` | string | Short units code |
| `seasonal_adjustment` | string | Seasonal adjustment method |
| `seasonal_adjustment_short` | string | Short seasonal adj. code |
| `last_updated` | string | Last data update timestamp |
| `popularity` | int | Popularity score |
| `notes` | string | Description/notes about the series |

**Search tips:**

- **Full-text search**: Use natural language terms like `"unemployment rate"`,
  `"consumer price index"`, or `"federal funds rate"`.
- **Series ID search**: Use `search_type="series_id"` when you know part of the
  series ID but not the exact code. For example, searching for `"GDP"` as a
  series ID will find `GDP`, `GDPC1`, `GDPPOT`, etc.
- **Be specific**: Adding qualifiers like `"monthly"`, `"annual"`, or
  `"seasonally adjusted"` helps narrow results when full-text searching.
- **No results**: If a query returns nothing, try broader terms or check for
  typos. FRED covers US and international economic data — try adding country
  context (e.g. `"GDP Japan"` instead of just `"GDP"`).

---

## 2. `get_series_info` — Series metadata

Retrieves detailed metadata for a specific FRED series by its series ID.

```bash
uv run scripts/fred_api.py ./gdp_info.json get_series_info "GDP"
```

**Arguments:**

- `series_id` (str, required) — FRED series ID (e.g. `"GDP"`, `"UNRATE"`,
  `"FEDFUNDS"`)

**Output:** `object` — a single series object with the same fields as the
search results above (`id`, `title`, `units`, `frequency`,
`seasonal_adjustment`, `notes`, `observation_start`, `observation_end`, etc.)

**Error handling:**

If the series ID does not exist in FRED, the function returns an error dict
with `"error"` and `"series_id"` keys and the process will exit with a
non-zero code.
