# Bulk Functions

Detailed argument specifications and output schemas for
`get_legislation_by_type`, `get_legislation_by_agency`, and
`search_by_geography`.

---

## 1. `get_legislation_by_type` — Filter by legislation type

Retrieves legislation filtered by type, optionally constrained to a specific
year.

```bash
# All Statutory Instruments
uv run scripts/legislation_api.py ./all_si.json get_legislation_by_type "SI" --limit 5

# Statutory Instruments from 2023
uv run scripts/legislation_api.py ./si_2023.json get_legislation_by_type "SI" --year "2023" --limit 10

# Scottish Acts from 2022
uv run scripts/legislation_api.py ./asp_2022.json get_legislation_by_type "ASP" --year "2022" --limit 20
```

**Arguments:**

- `type` (str, required) – legislation type code (see `search.md` for a full
  list of type values)
- `year` (str, default `""`) – optional year filter (e.g. `"2023"`)
- `limit` (int, default `20`) – maximum results to return

**Output:**

```json
{
  "total_results": 150,
  "results": [
    {
      "id": "uksi/2023/1",
      "title": "The Example Regulations 2023",
      "year": "2023",
      "type": "UK Statutory Instruments"
    }
  ]
}
```

**Common type codes:**

| Code   | Description                          |
|--------|--------------------------------------|
| `Acts` | All Acts (primary legislation)       |
| `SI`   | All Statutory Instruments            |
| `UKPGA`| UK Public General Acts               |
| `UKLA` | UK Local Acts                        |
| `ASP`  | Acts of the Scottish Parliament      |
| `ANAW` | Acts of the National Assembly for Wales |
| `NIA`  | Northern Ireland Acts               |
| `UKSI` | UK Statutory Instruments             |
| `SSI`  | Scottish Statutory Instruments       |
| `WSI`  | Welsh Statutory Instruments          |
| `NISI` | Northern Ireland Statutory Instruments |

---

## 2. `get_legislation_by_agency` — Legislation by government department

Retrieves legislation associated with a specific UK government department or
agency. This is useful for understanding the legislative output of a
particular department.

```bash
uv run scripts/legislation_api.py ./defra_legislation.json get_legislation_by_agency "Department for Environment, Food and Rural Affairs" --limit 5
```

**Arguments:**

- `agency` (str, required) – agency or department name. Common values include:
  - `"Department for Environment, Food and Rural Affairs"`
  - `"Department of Health and Social Care"`
  - `"Ministry of Justice"`
  - `"Department for Business and Trade"`
  - `"Department for Education"`
  - `"Department for Transport"`
  - `"Home Office"`
  - `"HM Treasury"`
  - `"Ministry of Defence"`
  - `"Department for Energy Security and Net Zero"`
  - `"Department for Work and Pensions"`
- `limit` (int, default `20`) – maximum results to return

**Output:**

```json
{
  "total_results": 45,
  "results": [
    {
      "id": "uksi/2023/100",
      "title": "The Environmental Targets (Biodiversity) (England) Regulations 2023",
      "year": "2023",
      "type": "UK Statutory Instruments",
      "agency": "Department for Environment, Food and Rural Affairs"
    }
  ]
}
```

**Usage notes:**

- Agency names should match the official UK government department name
- Results may include both primary and secondary legislation sponsored by
  the department
- Use `jq` to further filter or aggregate by year or type

---

## 3. `search_by_geography` — Search by applicable geography

Retrieves legislation applicable to a specific geography within the UK. This
is useful for finding legislation that applies to England, Scotland, Wales,
Northern Ireland, or the whole UK.

```bash
# Legislation applicable to Scotland
uv run scripts/legislation_api.py ./scotland_legislation.json search_by_geography "Scotland" --limit 5

# Legislation applicable to England only
uv run scripts/legislation_api.py ./england_legislation.json search_by_geography "England" --limit 10

# Wales
uv run scripts/legislation_api.py ./wales_legislation.json search_by_geography "Wales" --limit 5

# Northern Ireland
uv run scripts/legislation_api.py ./ni_legislation.json search_by_geography "Northern Ireland" --limit 5
```

**Arguments:**

- `geography` (str, required) – geography to filter by. Valid values:
  - `"England"`
  - `"Scotland"`
  - `"Wales"`
  - `"Northern Ireland"`
  - `"UK"` (or `"United Kingdom"`)
- `limit` (int, default `20`) – maximum results to return

**Output:**

```json
{
  "total_results": 320,
  "results": [
    {
      "id": "ssi/2023/1",
      "title": "The Example (Scotland) Regulations 2023",
      "year": "2023",
      "type": "Scottish Statutory Instruments",
      "geography": "Scotland"
    }
  ]
}
```

**Usage notes:**

- Use `"UK"` to find legislation that applies across the entire United Kingdom
- Use `"England"` for England-only legislation (often health, education, local
  government matters)
- Use `"Scotland"` / `"Wales"` / `"Northern Ireland"` for devolved legislation
- For Scottish Acts, also see `--type "ASP"` with `get_legislation_by_type`
- For Welsh Acts, also see `--type "ANAW"` with `get_legislation_by_type`

---

## Workflow Recipes

### Search → fetch full legislation

```bash
uv run scripts/legislation_api.py ./search.json search_legislation "carbon capture" --limit 3
ID=$(cat ./search.json | jq -r '.results[0].id // empty')
if [ -n "$ID" ]; then uv run scripts/legislation_api.py ./full.json get_legislation "$ID"; fi
```

### Year → type → changes analysis

```bash
# Get all Acts from 2008
uv run scripts/legislation_api.py ./acts_2008.json get_legislation_by_year "2008" --type "Acts" --limit 5
# Get changes for a specific Act from the results
ID=$(cat ./acts_2008.json | jq -r '.results[0].id // empty')
if [ -n "$ID" ]; then uv run scripts/legislation_api.py ./changes.json get_legislation_changes "$ID"; fi
```

### Geography + type cross-section

```bash
# Find Scottish Statutory Instruments
uv run scripts/legislation_api.py ./scotland_leg.json search_by_geography "Scotland" --limit 20
cat ./scotland_leg.json | jq '[.results[] | select(.type | contains("Scottish Statutory Instrument"))]'
```

### Type-based bulk with filtering

```bash
# Get all UK Statutory Instruments from 2023
uv run scripts/legislation_api.py ./si_2023.json get_legislation_by_type "UKSI" --year "2023" --limit 50
# Extract just the IDs for further processing
cat ./si_2023.json | jq -r '[.results[].id]'
```
