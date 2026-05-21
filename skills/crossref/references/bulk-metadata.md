# Bulk & Metadata Functions

Detailed argument specifications, output schemas, and usage guidance for
`get_agency`, `list_works_by_prefix`, and `get_work_type_distribution`.

## 1. `get_agency` — DOI registration agency lookup

Finds which registration agency manages a given DOI. CrossRef is one of many
DOI registration agencies — others include DataCite, ISTIC, and mEDRA. Use
this when you need to determine where to look for metadata about a DOI.

```bash
uv run scripts/crossref_api.py ./agency_10_1038.json get_agency "10.1038/nature12373"
uv run scripts/crossref_api.py ./agency_datacite.json get_agency "10.5281/zenodo.1234567"
```

**Arguments:**

-   `doi` (str, required) — DOI to look up (e.g. `"10.1038/nature12373"`)

**Output:** `object` — agency metadata:

-   `DOI` (str) — the DOI that was queried
-   `agency` (object) — registration agency information
    -   `id` (str) — agency identifier
    -   `label` (str) — agency name (e.g. `"CrossRef"`, `"DataCite"`,
        `"ISTIC"`, `"mEDRA"`)
    -   `member` (str | null) — CrossRef member ID if applicable

**Usage tip**: Use this to check if a DOI is managed by CrossRef before calling
`get_work`. Non-CrossRef DOIs (e.g. DataCite DOIs for datasets) will return a
different agency, and you should use the appropriate API for that agency.

---

## 2. `list_works_by_prefix` — Works under a DOI prefix

Lists works registered under a specific DOI prefix. Use this to discover all
works from a specific publisher or organization that controls a given prefix.

```bash
uv run scripts/crossref_api.py ./prefix_10_1038.json list_works_by_prefix "10.1038" --limit 10
uv run scripts/crossref_api.py ./prefix_10_1016.json list_works_by_prefix "10.1016" --limit 5
```

**Arguments:**

-   `prefix` (str, required) — DOI prefix (e.g. `"10.1038"` for Nature,
    `"10.1016"` for Elsevier)
-   `limit` (int, default 20) — maximum results to return

**Output:** `list[object]` — list of work objects with the same structure as
`search_works` results (DOI, title, author, type, container, etc.)

**Common DOI prefixes:**

| Prefix | Organization |
|--------|-------------|
| `10.1038` | Springer Nature / Nature journals |
| `10.1016` | Elsevier |
| `10.1021` | American Chemical Society |
| `10.1073` | PNAS / National Academy of Sciences |
| `10.1101` | Cold Spring Harbor Laboratory / bioRxiv |
| `10.1126` | American Association for the Advancement of Science / Science |
| `10.1002` | Wiley |
| `10.1186` | BioMed Central |
| `10.1371` | PLOS |
| `10.1039` | Royal Society of Chemistry |
| `10.1088` | IOP Publishing |
| `10.1080` | Taylor & Francis |
| `10.1177` | SAGE Publishing |
| `10.1093` | Oxford University Press |
| `10.5281` | Zenodo / DataCite |

---

## 3. `get_work_type_distribution` — Type distribution for a query

Returns the distribution of work types (journal-article, book-chapter, dataset,
dissertation, etc.) for a given query, using CrossRef's facet feature. Use this
to understand the composition of results before deciding which types to focus
on.

```bash
uv run scripts/crossref_api.py ./cancer_type_dist.json get_work_type_distribution "cancer"
uv run scripts/crossref_api.py ./machine_learning_types.json get_work_type_distribution "machine learning"
```

**Arguments:**

-   `query` (str, required) — query string to get type distribution for

**Output:** `object` — mapping of work type names to count values:

```json
{
  "journal-article": 145000,
  "book-chapter": 3200,
  "proceedings-article": 1500,
  "dataset": 800,
  "dissertation": 500,
  "posted-content": 300,
  "reference-book": 120,
  "report": 80,
  "book": 60,
  "monograph": 45
}
```

**Common work types:** `journal-article`, `book-chapter`,
`proceedings-article`, `dataset`, `dissertation`, `posted-content` (preprints),
`reference-book`, `report`, `book`, `monograph`, `book-series`, `book-set`,
`component`, `grant`, `peer-review`, `standard`, `other`.

**Usage tip**: Use the type distribution to decide which filter to apply in
`search_works`. For example, if there are many datasets, you might want to
search with `--filter "type:dataset"`:

```bash
cat ./cancer_type_dist.json | jq 'to_entries | sort_by(-.value) | .[:5]'
```
