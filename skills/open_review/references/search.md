# Search Functions

Detailed argument specifications, output schemas, search strategies, and
troubleshooting for `search_notes`, `get_note`, and `get_venue`.

## 1. `search_notes` — Search papers/reviews by query

Searches the OpenReview notes index for papers, reviews, comments, and other
notes matching a free-text query. Optionally filter by venue ID to restrict
results to a specific conference or workshop.

```bash
uv run scripts/openreview_api.py ./search_results.json search_notes "transformer" --limit 5
uv run scripts/openreview_api.py ./search_results.json search_notes "attention mechanism" --venue "ICLR.cc/2024/Conference" --limit 10
```

**Arguments:**

- `query` (str, required) — Free-text search query
- `venue` (str, optional, default "") — Venue ID to restrict results (e.g.
  `"ICLR.cc/2024/Conference"`, `"NeurIPS.cc/2023/Conference"`)
- `limit` (int, default 20) — Maximum number of notes to return

**Output:** `dict` — contains a `notes` list and a `count` field.
Each note typically includes the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique note identifier |
| `forum` | string | Forum ID (ID of the original paper submission) |
| `replyto` | string or null | Parent note ID this note replies to |
| `tcdate` | int | Timestamp of creation (Unix milliseconds) |
| `tmdate` | int | Timestamp of last modification (Unix milliseconds) |
| `writers` | list[string] | Groups/users who can modify this note |
| `signatures` | list[string] | Groups/users who signed this note |
| `readers` | list[string] | Groups/users who can read this note |
| `content` | dict | Note-specific content fields (varies by note type) |

> ⚠️ Note: `content` structure varies depending on the note type and venue.
> For a submission (paper): typically includes `title`, `abstract`, `authors`,
> `authorids`, `keywords`, `pdf`, `venue`, and `venueid`.
> For reviews: typically includes `review`, `rating`, `confidence`,
> `recommendation`, and other review-specific fields.
> Access to non-public fields requires a valid `OPENREVIEW_API_KEY`.

**Filtering tips:**

- Use the `venue` parameter to restrict results to a specific conference rather
  than searching across all of OpenReview.
- For more targeted results, use specific queries that include paper titles,
  author names, or keywords.

**Common venue IDs:**

| Venue | Venue ID |
|-------|----------|
| ICLR 2024 | `ICLR.cc/2024/Conference` |
| ICLR 2025 | `ICLR.cc/2025/Conference` |
| NeurIPS 2023 | `NeurIPS.cc/2023/Conference` |
| NeurIPS 2024 | `NeurIPS.cc/2024/Conference` |
| ICML 2024 | `ICML.cc/2024/Conference` |
| COLM 2024 | `COLM.cc/2024/Conference` |

--------------------------------------------------------------------------------

## 2. `get_note` — Retrieve full details of a single note

Fetches the complete note object including all content fields. For paper
submissions this includes title, abstract, authors, and PDF link. For reviews
this includes the review text, rating, and confidence.

```bash
uv run scripts/openreview_api.py ./note.json get_note "S3ff6d1234567890abcdef1234567890ab"
```

**Arguments:**

- `note_id` (str, required) — The note ID to retrieve

**Output:** `dict` — single note object with all fields. Same structure as
individual note entries in `search_notes` results.

**Output example:**

```json
{
  "id": "S3ff6d1234567890abcdef1234567890ab",
  "forum": "S3ff6d1234567890abcdef1234567890ab",
  "content": {
    "title": "Attention Is All You Need",
    "abstract": "The dominant sequence transduction models...",
    "authors": ["Author Name"],
    "authorids": ["~Author_Name1"],
    "venueid": "ICLR.cc/2024/Conference"
  },
  "signatures": ["~Author_Name1"],
  "writers": ["~Author_Name1"],
  "readers": ["everyone"],
  "tcdate": 1700000000000,
  "tmdate": 1700000000000
}
```

--------------------------------------------------------------------------------

## 3. `get_venue` — Retrieve venue/conference metadata

Fetches details about a specific venue/conference including its name, short
name, and other metadata.

```bash
uv run scripts/openreview_api.py ./venue.json get_venue "ICLR.cc/2024/Conference"
```

**Arguments:**

- `venue_id` (str, required) — The venue ID (e.g.
  `"ICLR.cc/2024/Conference"`, `"NeurIPS.cc/2023/Conference"`)

**Output:** `dict` — single venue object with metadata fields.

**Output example:**

```json
{
  "id": "ICLR.cc/2024/Conference",
  "short_name": "ICLR 2024",
  "website_url": "https://iclr.cc/Conferences/2024",
  "contact": "info@iclr.cc"
}
```
