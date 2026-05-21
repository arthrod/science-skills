# Categories & Releases Functions

Detailed argument specifications, output schemas, and usage guidance for
`get_category`, `get_category_series`, `get_releases`, and `get_release`.

## 1. `get_category` — Category tree

Retrieves a category and its immediate child categories. FRED categories
form a tree structure. The root category is ID 0.

```bash
uv run scripts/fred_api.py ./root_category.json get_category 0
uv run scripts/fred_api.py ./output_category.json get_category 1
```

**Arguments:**

- `category_id` (int, required) — Category ID. Use `0` for the root
  category to explore the full tree.

**Output:** `list[object]` — list of categories (parent + children), each
with:

| Key | Type | Description |
|-----|------|-------------|
| `id` | int | Category ID |
| `name` | string | Category name |
| `parent_id` | int | Parent category ID (`0` for root categories) |

**Exploring the category tree:**

1. Start with `get_category 0` to get root categories.
2. Pick a category ID from the results and call `get_category <id>`.
3. Repeat to drill deeper.

Example root categories (IDs may vary):
- `1` — Output
- `2` — Employment
- `3` — Population
- `4` — Income
- `5` — Prices
- `6` — Financial

---

## 2. `get_category_series` — Series in a category

Retrieves all FRED series belonging to a specific category.

```bash
uv run scripts/fred_api.py ./output_series.json get_category_series 1 --limit 10
```

**Arguments:**

- `category_id` (int, required) — Category ID
- `limit` (int, default 25) — Maximum series to return (max 1000)

**Output:** `list[object]` — list of series dicts with the same fields as
search results: `id`, `title`, `units`, `frequency`,
`seasonal_adjustment`, `observation_start`, `observation_end`, `popularity`,
`notes`, etc.

---

## 3. `get_releases` — All economic releases

Lists all economic releases available in FRED. Releases are groups of
related series (e.g. "Gross Domestic Product" release contains GDP, GDPC1,
GDPDEF, etc.).

```bash
uv run scripts/fred_api.py ./all_releases.json get_releases --limit 50
```

**Arguments:**

- `limit` (int, default 25) — Maximum number of releases to return
  (max 1000)

**Output:** `list[object]` — each with:

| Key | Type | Description |
|-----|------|-------------|
| `id` | int | Release ID |
| `realtime_start` | string | Real-time start |
| `realtime_end` | string | Real-time end |
| `name` | string | Release name (e.g. `"Employment Situation"`) |
| `press_release` | string | Whether a press release is available |
| `link` | string | URL to release information |
| `notes` | string | Release description / notes |

---

## 4. `get_release` — A specific release

Returns metadata for a single economic release.

```bash
uv run scripts/fred_api.py ./release_51.json get_release 51
```

**Arguments:**

- `release_id` (int, required) — Release ID (e.g. `51` for "Gross
  Domestic Product", `53` for "Consumer Price Index", `50` for "Employment
  Situation")

**Output:** `object` — a single release dict with `id`, `name`,
`press_release`, `link`, `notes`, etc.

**Common release IDs:**

| ID | Release Name |
|----|-------------|
| 50 | Employment Situation |
| 51 | Gross Domestic Product |
| 52 | Consumer Price Index |
| 53 | Personal Income and Outlays |
| 54 | Producer Price Index |
| 55 | Retail Sales |
| 56 | Industrial Production and Capacity Utilization |
| 57 | Housing Starts |

**Usage pattern**: Find a release via `get_releases` or use a known release
ID, then use `get_series_info` or `search_series` to find specific series
within that release.
