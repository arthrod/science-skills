# Search Functions

Detailed argument specifications, output schemas, and troubleshooting for
`search_legislation`, `get_legislation`, and `get_legislation_types`.

---

## 1. `search_legislation` — Find legislation by keyword query

Returns a list of legislation matching a free-text query. Supports keyword
search across UK legislation titles and content.

```bash
uv run scripts/legislation_api.py ./search_results.json search_legislation "climate change" --limit 5
```

**Arguments:**

- `query` (str, required) – free-text search query
- `year` (str, default `""`) – optional year filter (e.g. `"2023"`)
- `type` (str, default `""`) – optional legislation type filter (e.g. `"Acts"`,
  `"SI"`)
- `limit` (int, default `20`) – maximum results to return

**Output:**

```json
{
  "total_results": 142,
  "results": [
    {
      "id": "ukpga/2008/27",
      "title": "Climate Change Act 2008",
      "year": "2008",
      "type": "UK Public General Acts"
    }
  ]
}
```

**Filtering tips:**

- Use `--type "Acts"` to restrict to primary legislation
- Use `--type "SI"` for Statutory Instruments
- Use `--year "2023"` to narrow to a specific year
- Combine: `--year "2023" --type "Acts"`

**Alternative URL patterns (legislation.gov.uk also supports):**

- Search across all primary legislation:
  `https://www.legislation.gov.uk/primary?search={query}`
- Search across all secondary legislation:
  `https://www.legislation.gov.uk/secondary?search={query}`

These alternative patterns can be useful for broad category browsing, but the
`search_legislation` wrapper is the recommended approach for structured queries.

---

## 2. `get_legislation` — Full text of a specific piece of legislation

Retrieves the full metadata and text content of a piece of legislation by its
legislation.gov.uk identifier.

```bash
uv run scripts/legislation_api.py ./ukpga_2023_1.json get_legislation "ukpga/2023/1"
```

**Arguments:**

- `legislation_id` (str, required) – legislation identifier in path format.
  Common ID patterns:
  - `ukpga/2023/1` – UK Public General Act (year/number)
  - `ukpga/2008/27` – Climate Change Act 2008
  - `uksi/2023/1` – UK Statutory Instrument
  - `asp/2023/1` – Act of the Scottish Parliament
  - `anaw/2023/1` – Act of the National Assembly for Wales
  - `nia/2023/1` – Northern Ireland Act
  - `ssi/2023/1` – Scottish Statutory Instrument
  - `wsi/2023/1` – Welsh Statutory Instrument

**Output:**

Returns the full legislation JSON document including title, year, type, and
complete text content. The schema varies by legislation type but typically
includes:

```json
{
  "title": "Finance Act 2023",
  "year": "2023",
  "number": "1",
  "type": "UK Public General Acts",
  "content": "..."
}
```

---

## 3. `get_legislation_types` — List available legislation types

Returns the list of legislation types available on legislation.gov.uk.

```bash
uv run scripts/legislation_api.py ./types.json get_legislation_types --limit 10
```

**Arguments:**

- `limit` (int, default `50`) – maximum types to return

**Output:**

```json
{
  "types": [
    "UK Public General Acts",
    "UK Local Acts",
    "Acts of the Scottish Parliament",
    "Acts of the National Assembly for Wales",
    "Northern Ireland Acts",
    "UK Statutory Instruments",
    "Scottish Statutory Instruments",
    "Welsh Statutory Instruments",
    "Northern Ireland Statutory Instruments",
    "Church Instruments"
  ],
  "total": 10
}
```

Common type values to use with `--type` in other functions:

| Type value         | Description                              |
|--------------------|------------------------------------------|
| `Acts`             | All types of Acts                        |
| `SI`               | All Statutory Instruments                |
| `UKPGA`            | UK Public General Acts                   |
| `UKLA`             | UK Local Acts                            |
| `ASP`              | Acts of the Scottish Parliament          |
| `ANAW`             | Acts of the National Assembly for Wales  |
| `NIA`              | Northern Ireland Acts                    |
| `UKSI`             | UK Statutory Instruments                 |
| `SSI`              | Scottish Statutory Instruments           |
| `WSI`              | Welsh Statutory Instruments              |
| `NISI`             | Northern Ireland Statutory Instruments   |
