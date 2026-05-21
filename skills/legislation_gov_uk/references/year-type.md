# By Year & Type Functions

Detailed argument specifications and output schemas for
`get_legislation_by_year`, `get_legislation_changes`, and
`get_legislation_versions`.

---

## 1. `get_legislation_by_year` — All legislation from a given year

Retrieves a list of legislation enacted in a specific year, with optional type
filtering.

```bash
# All legislation from 2023
uv run scripts/legislation_api.py ./legislation_2023.json get_legislation_by_year "2023" --limit 5

# Only Acts from 2023
uv run scripts/legislation_api.py ./acts_2023.json get_legislation_by_year "2023" --type "Acts" --limit 10
```

**Arguments:**

- `year` (str, required) – the year to query (e.g. `"2023"`)
- `type` (str, default `""`) – optional type filter (e.g. `"Acts"`, `"SI"`)
- `limit` (int, default `20`) – maximum results to return

**Output:**

```json
{
  "total_results": 35,
  "results": [
    {
      "id": "ukpga/2023/1",
      "title": "Finance Act 2023",
      "year": "2023",
      "type": "UK Public General Acts"
    },
    {
      "id": "ukpga/2023/2",
      "title": "Example Act 2023",
      "year": "2023",
      "type": "UK Public General Acts"
    }
  ]
}
```

**Filtering tips:**

- Use `--type "Acts"` to get only primary legislation for a year
- Use `--type "SI"` to get only Statutory Instruments for a year
- Use `--type "UKPGA"` for UK Public General Acts only
- Combine with `jq` to further refine: `cat results.json | jq '[.results[] | select(.type | contains("Scottish"))]'`

---

## 2. `get_legislation_changes` — Amendments and changes over time

Retrieves the full amendment history for a piece of legislation, including
which other instruments have amended it and when.

```bash
uv run scripts/legislation_api.py ./climate_act_changes.json get_legislation_changes "ukpga/2008/27"
```

**Arguments:**

- `legislation_id` (str, required) – legislation identifier in path format
  (e.g. `"ukpga/2008/27"` for the Climate Change Act 2008)

**Output:**

Returns a JSON document describing the amendment history. The structure
varies depending on the legislation but typically includes timelines of
modifications, lists of amending instruments, and effective dates.

```json
{
  "legislation": "ukpga/2008/27",
  "title": "Climate Change Act 2008",
  "changes": []
}
```

**Usage notes:**

- Use this function to understand how legislation has evolved
- Particularly useful for tracing amendments to framework acts
- Results can be combined with `get_legislation_versions` to retrieve specific
  historic versions

---

## 3. `get_legislation_versions` — Available versions of legislation

Retrieves all available versions (historical snapshots) of a piece of
legislation, including the original enactment and any amended versions.

```bash
uv run scripts/legislation_api.py ./climate_act_versions.json get_legislation_versions "ukpga/2008/27"
```

**Arguments:**

- `legislation_id` (str, required) – legislation identifier in path format
  (e.g. `"ukpga/2008/27"` for the Climate Change Act 2008)

**Output:**

Returns a JSON document listing all available versions of the legislation,
including version dates and status.

```json
{
  "legislation": "ukpga/2008/27",
  "title": "Climate Change Act 2008",
  "versions": [
    {
      "date": "2008-11-26",
      "status": "Original",
      "description": "Original enactment"
    },
    {
      "date": "2019-06-27",
      "status": "Amended",
      "description": "Amendment by Climate Change Act 2008 (2050 Target Amendment) Order 2019"
    }
  ]
}
```

**Usage notes:**

- Use this to discover which historical snapshots are available
- To retrieve a specific version, combine the version date with
  `get_legislation` using appropriate URL parameters
- The original ("as enacted") version is always available
- Amended versions reflect the legislation as it stood at a given point in time
