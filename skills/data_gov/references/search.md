# Search Functions

Detailed argument specifications, output schemas, and troubleshooting for
`search_datasets`, `get_dataset`, and `get_dataset_show`.

---

## 1. `search_datasets` — Search US government datasets

Returns a list of datasets matching a free-text query, with optional filters
by topic and file format. Uses the CKAN `package_search` action.

```bash
uv run scripts/data_gov_api.py ./search_results.json search_datasets "climate change" --limit 5

# With topic filter
uv run scripts/data_gov_api.py ./search_results.json search_datasets "education" --topic agriculture --limit 10

# With format filter
uv run scripts/data_gov_api.py ./search_results.json search_datasets "population" --format CSV --limit 20
```

**Arguments:**

-   `query` (str, required) — Free-text search query for datasets
-   `topic` (str, optional) — Filter by topic/category name
-   `format` (str, optional) — Filter by resource file format (e.g. CSV, JSON,
    PDF, XML, ZIP)
-   `limit` (int, default 20) — Maximum number of results to return

**Output:** List of dataset dicts, each containing:

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Dataset UUID |
| `name` | str | Dataset URL slug name |
| `title` | str | Human-readable title |
| `notes` | str | Description/abstract |
| `organization` | dict | Organization metadata (title, name, id) |
| `resources` | list | List of resource file dicts |
| `tags` | list | List of tag dicts with name |
| `groups` | list | List of group/category dicts |
| `metadata_created` | str | ISO date created |
| `metadata_modified` | str | ISO date last modified |
| `url` | str or null | Landing page URL |

**Filtering tips:**

-   Use `topic` to narrow results to a specific category (e.g. agriculture,
    health, energy, climate, education).
-   Use `format` to find only datasets available in a specific file format.
    Common formats: `CSV`, `JSON`, `XML`, `PDF`, `ZIP`, `GeoJSON`, `SHP`,
    `KML`, `HTML`.

**Troubleshooting:**

-   If a query returns few results, try broader keywords.
-   Avoid overly specific phrases; CKAN search uses full-text indexing.
-   Some datasets may not have an `organization` field (returns `null`).

---

## 2. `get_dataset` — Get dataset metadata by ID

Retrieves full metadata for a specific dataset using the CKAN `package_show`
action. Includes all resources, tags, groups, and organization.

```bash
uv run scripts/data_gov_api.py ./dataset.json get_dataset "db24c0d1-2c29-4c76-9ceb-f5f36504978c"

# By name (slug) also works
uv run scripts/data_gov_api.py ./dataset.json get_dataset "climate-change-indicators"
```

**Arguments:**

-   `dataset_id` (str, required) — Dataset UUID or slug name

**Output:** Dict with full dataset metadata (same schema as individual search
result items, but with all resources and metadata included).

**Usage tips:**

-   Use this after `search_datasets` to get full details on specific results.
-   Use `jq` to extract download URLs: `cat dataset.json | jq '.resources[].url'`
-   Use `jq` to extract resource formats: `cat dataset.json | jq '[.resources[] | {url, format, description}]'`

---

## 3. `get_dataset_show` — Package details by ID or name

Alias for `get_dataset`. Uses the CKAN `package_show` action.

```bash
uv run scripts/data_gov_api.py ./package.json get_dataset_show "my-package-name"
```

**Arguments:**

-   `package_id` (str, required) — Package ID or name

**Output:** Same as `get_dataset`.
