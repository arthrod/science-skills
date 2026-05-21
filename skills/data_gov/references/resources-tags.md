# Resources & Tags Functions

Detailed argument specifications and output schemas for `get_resource`,
`search_tags`, `list_tags`, and `get_recent_datasets`.

---

## 1. `get_resource` — Get resource file details

Retrieves metadata about a specific resource file within a dataset. Uses the
CKAN `resource_show` action.

```bash
uv run scripts/data_gov_api.py ./resource.json get_resource "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Arguments:**

-   `resource_id` (str, required) — Resource UUID

**Output:** Dict with fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Resource UUID |
| `name` | str | Resource name/title |
| `description` | str or null | Resource description |
| `format` | str | File format (e.g. CSV, JSON, PDF, ZIP) |
| `url` | str | Direct download URL |
| `size` | int or null | File size in bytes |
| `created` | str | ISO date created |
| `last_modified` | str | ISO date last modified |
| `package_id` | str | Parent dataset UUID |
| `resource_type` | str or null | Resource type |
| `mimetype` | str or null | MIME type |

**Usage tips:**

-   Use the `url` field to download the actual data file.
-   Use `format` to check if the file is in a usable format before downloading.
-   Resource IDs can be obtained from `search_datasets` or `get_dataset` results
    in the `resources` array.

---

## 2. `search_tags` — Search by keyword tag

Searches datasets by a keyword tag. Uses the CKAN `tag_show` action. Returns
tag metadata and datasets associated with matching tags.

```bash
uv run scripts/data_gov_api.py ./tag_results.json search_tags "water"

# With custom limit
uv run scripts/data_gov_api.py ./tag_results.json search_tags "energy" --limit 10
```

**Arguments:**

-   `query` (str, required) — Tag keyword to search for
-   `limit` (int, default 20) — Maximum number of datasets to return

**Output:** List of dataset dicts associated with the matching tag. Each
dataset dict contains the same fields as a search result (title, id, name,
organization, resources, etc.).

**Usage tips:**

-   Tags are keywords applied to datasets by publishers.
-   Common tags include: `water`, `energy`, `climate`, `agriculture`,
    `transportation`, `health`, `education`, `population`.
-   If no results are found, try a different keyword (tags are exact match).

---

## 3. `list_tags` — List all tags

Lists all tags used across Data.gov. Uses the CKAN `tag_list` action.

```bash
uv run scripts/data_gov_api.py ./tags.json list_tags --limit 100

# With default limit (50)
uv run scripts/data_gov_api.py ./tags.json list_tags
```

**Arguments:**

-   `limit` (int, default 50) — Maximum number of tags to return

**Output:** List of tag name strings. Example:

```json
["water", "energy", "climate", "agriculture", "health", "education"]
```

**Usage tips:**

-   Use to discover available tags before calling `search_tags`.
-   Tags are returned as plain strings (not dicts), unlike in dataset objects.

---

## 4. `get_recent_datasets` — Recently added/updated

Retrieves the most recently created or updated datasets with their resources
included. Uses the CKAN `current_package_list_with_resources` action.

```bash
uv run scripts/data_gov_api.py ./recent.json get_recent_datasets --limit 10

# With default limit (20)
uv run scripts/data_gov_api.py ./recent.json get_recent_datasets
```

**Arguments:**

-   `limit` (int, default 20) — Maximum number of datasets to return

**Output:** List of recent dataset dicts, each with full resource metadata
(same schema as `get_dataset` results). Includes all resource file details
(name, format, URL, size) embedded in each dataset.

**Usage tips:**

-   Useful for discovering newly published government data.
-   Run periodically to track updates to the Data.gov catalog.
-   Each result includes `resources` with download URLs.
