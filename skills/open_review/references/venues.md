# Venue Functions

Detailed argument specifications, output schemas, and strategies for
`get_venue_notes`, `get_venue_groups`, and `list_venues`.

## 1. `get_venue_notes` — Get papers/reviews by venue

Fetches notes associated with a specific venue, optionally filtered by
submission stage. Common stages include:

- `"Submission"` — Paper submissions
- `"Decision"` — Decision notifications (accept/reject)
- `"Withdrawal"` — Withdrawn submissions
- `"DeskRejected"` — Desk-rejected submissions

```bash
uv run scripts/openreview_api.py ./venue_notes.json get_venue_notes "ICLR.cc/2024/Conference" --stage "Submission" --limit 100
uv run scripts/openreview_api.py ./decisions.json get_venue_notes "ICLR.cc/2024/Conference" --stage "Decision" --limit 50
```

**Arguments:**

- `venue_id` (str, required) — The venue ID (e.g.
  `"ICLR.cc/2024/Conference"`)
- `stage` (str, optional, default "") — Submission stage filter
  (`"Submission"`, `"Decision"`, `"Withdrawal"`, `"DeskRejected"`, etc.)
- `limit` (int, default 20) — Maximum number of notes to return

**Output:** `dict` — contains a `notes` list and a `count` field. Each note
follows the same structure as [search_notes](search.md#1-search_notes--search-papersreviews-by-query) output.

**Pagination:**

The OpenReview API paginates results. The response includes `count` (total
number of matching notes) and the returned notes array. For large venues,
use multiple calls with increasing `offset` parameter if supported, or rely
on the `limit` parameter to control batch size.

--------------------------------------------------------------------------------

## 2. `get_venue_groups` — Get venue groups/committees

Fetches all groups (committees, roles) associated with a venue. This includes
reviewers, area chairs, program committee members, and other roles.

```bash
uv run scripts/openreview_api.py ./venue_groups.json get_venue_groups "ICLR.cc/2024/Conference"
```

**Arguments:**

- `venue_id` (str, required) — The venue ID (e.g.
  `"ICLR.cc/2024/Conference"`)

**Output:** `dict` — contains a `groups` list. Each group includes:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Group identifier |
| `members` | list[string] | Group members (user IDs or nested groups) |
| `signatures` | list[string] | Signatures for this group |
| `writers` | list[string] | Writers for this group |
| `readers` | list[string] | Readers for this group |
| `tcdate` | int | Creation timestamp (Unix milliseconds) |
| `tmdate` | int | Last modification timestamp (Unix milliseconds) |

**Common venue group patterns:**

- `{venue_id}/Reviewers`
- `{venue_id}/Area_Chairs`
- `{venue_id}/Program_Chairs`
- `{venue_id}/Authors`

--------------------------------------------------------------------------------

## 3. `list_venues` — List available venues/conferences

Returns all venues/conferences in the OpenReview system.

```bash
uv run scripts/openreview_api.py ./venues.json list_venues --limit 100
```

**Arguments:**

- `limit` (int, default 50) — Maximum number of venues to return

**Output:** `dict` — contains a `venues` list. Each venue includes:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Venue identifier |
| `short_name` | string | Short/abbreviated venue name |
| `website_url` | string or null | Venue website URL |
| `contact` | string or null | Contact email |
| `domain` | string or null | Venue domain |
| `program_chairs` | list[string] or null | Program chair email(s) |

**Output example:**

```json
{
  "venues": [
    {"id": "ICLR.cc/2024/Conference", "short_name": "ICLR 2024"},
    {"id": "NeurIPS.cc/2023/Conference", "short_name": "NeurIPS 2023"}
  ],
  "count": 2
}
```
