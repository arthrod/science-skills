# Organizations & Groups Functions

Detailed argument specifications and output schemas for `get_organization`,
`list_organizations`, `get_group`, and `list_groups`.

---

## 1. `get_organization` — Get agency/department details

Retrieves metadata about a specific organization (federal agency or department)
and its datasets. Uses the CKAN `organization_show` action.

```bash
uv run scripts/data_gov_api.py ./org.json get_organization "environmental-protection-agency"

# By organization ID
uv run scripts/data_gov_api.py ./org.json get_organization "epa"
```

**Arguments:**

-   `org_name` (str, required) — Organization name, slug, or ID

**Output:** Dict with fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Organization UUID |
| `name` | str | URL slug name |
| `title` | str | Display name (e.g. "Environmental Protection Agency") |
| `description` | str or null | Organization description |
| `image_url` | str or null | Logo/image URL |
| `packages` | list | List of dataset dicts belonging to this org |
| `created` | str | ISO date created |
| `state` | str | Active/deleted state |

**Usage tips:**

-   Use to discover all datasets published by a specific agency.
-   Common organizations: `department-of-energy`, `noaa`, `usgs`,
    `environmental-protection-agency`, `nasa`, `department-of-transportation`.

---

## 2. `list_organizations` — List all organizations

Lists all organizations (agencies/departments) on Data.gov. Uses the CKAN
`organization_list` action.

```bash
uv run scripts/data_gov_api.py ./orgs.json list_organizations --limit 100

# With default limit (50)
uv run scripts/data_gov_api.py ./orgs.json list_organizations
```

**Arguments:**

-   `limit` (int, default 50) — Maximum number of organizations to return

**Output:** List of organization dicts, each with:

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Organization UUID |
| `name` | str | URL slug name |
| `title` | str | Display name |
| `description` | str or null | Description |
| `image_url` | str or null | Logo URL |
| `state` | str | Active/deleted state |
| `display_name` | str | Display name (usually same as title) |

---

## 3. `get_group` — Get topic category details

Retrieves metadata about a specific group (topic/category) and its datasets.
Uses the CKAN `group_show` action.

```bash
uv run scripts/data_gov_api.py ./group.json get_group "climate"

# By group ID
uv run scripts/data_gov_api.py ./group.json get_group "climate5431"
```

**Arguments:**

-   `group_name` (str, required) — Group name, slug, or ID

**Output:** Dict with fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Group UUID |
| `name` | str | URL slug name |
| `title` | str | Display name |
| `description` | str or null | Group description |
| `packages` | list | List of dataset dicts in this group |
| `created` | str | ISO date created |
| `state` | str | Active/deleted state |

---

## 4. `list_groups` — List all groups

Lists all groups (topics/categories) on Data.gov. Uses the CKAN `group_list`
action.

```bash
uv run scripts/data_gov_api.py ./groups.json list_groups --limit 100

# With default limit (50)
uv run scripts/data_gov_api.py ./groups.json list_groups
```

**Arguments:**

-   `limit` (int, default 50) — Maximum number of groups to return

**Output:** List of group dicts, each with:

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Group UUID |
| `name` | str | URL slug name |
| `title` | str | Display name |
| `description` | str or null | Description |
| `state` | str | Active/deleted state |
| `display_name` | str | Display name |
