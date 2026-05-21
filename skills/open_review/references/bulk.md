# Bulk Functions

Detailed argument specifications, output schemas, and strategies for
`search_notes_by_group`, `get_notes_by_forum`, and `get_group`.

## 1. `search_notes_by_group` — Get notes by a specific group

Fetches all notes authored by members of a specified group. This is useful for
retrieving all reviews from a group of reviewers, or all papers by a research
group.

```bash
uv run scripts/openreview_api.py ./group_notes.json search_notes_by_group "ICLR.cc/2024/Conference/Reviewers" --limit 100
```

**Arguments:**

- `group_id` (str, required) — The group ID whose members' notes to retrieve
- `limit` (int, default 50) — Maximum number of notes to return

**Output:** `dict` — contains a `notes` list and a `count` field. Each note
follows the same structure as described in [search.md](search.md#1-search_notes--search-papersreviews-by-query).

**Common group ID patterns:**

| Group Type | Group ID Pattern |
|------------|------------------|
| Reviewers | `{venue_id}/Reviewers` |
| Area Chairs | `{venue_id}/Area_Chairs` |
| Program Chairs | `{venue_id}/Program_Chairs` |
| Authors | `{venue_id}/Authors` |

**Tip:** Use `get_venue_groups` first to discover available groups for a venue.

--------------------------------------------------------------------------------

## 2. `get_notes_by_forum` — Get all notes in a forum thread

Retrieves all notes belonging to the same forum thread. The forum ID is the
note ID of the original paper submission (i.e., the top-level note). This
returns the complete thread including:

- The original paper submission
- All reviews
- Meta-reviews/area chair summaries
- Author responses/rebuttals
- Decision notifications (accept/reject)
- Public comments

```bash
uv run scripts/openreview_api.py ./forum_thread.json get_notes_by_forum "S3ff6d1234567890abcdef1234567890ab"
```

**Arguments:**

- `forum_id` (str, required) — The forum ID (note ID of the original paper
  submission)

**Output:** `dict` — contains a `notes` list with all notes in the forum,
sorted by creation date (ascending). Each note includes:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Note identifier |
| `forum` | string | Forum ID (same for all notes in thread) |
| `replyto` | string or null | Parent note ID (null for the original submission) |
| `signatures` | list[string] | Authors/signers of the note |
| `content` | dict | Note content (varies by type) |
| `tcdate` | int | Creation timestamp |
| `tmdate` | int | Last modification timestamp |

**Thread structure:**

The original forum note (`replyto` is null) is the paper submission. All other
notes in the thread have `replyto` pointing to another note. Reviews typically
have `replyto` pointing to the forum root. Author responses may point to
individual reviews or to the forum root.

**Example: Slimming reviews from a forum thread:**

```bash
# Extract just the review content from a forum thread
cat ./forum_thread.json | jq '[.notes[] | select(.content.review != null) | {id, review: .content.review, rating: .content.rating, confidence: .content.confidence}]'
```

```bash
# Extract the decision (accept/reject) from a forum thread
cat ./forum_thread.json | jq '[.notes[] | select(.content.decision != null) | {decision: .content.decision}]'
```

--------------------------------------------------------------------------------

## 3. `get_group` — Get group information

Fetches metadata about a specific group including its members, parent groups,
and access permissions.

```bash
uv run scripts/openreview_api.py ./group.json get_group "ICLR.cc/2024/Conference/Reviewers"
```

**Arguments:**

- `group_id` (str, required) — The group ID

**Output:** `dict` — single group object. Fields include:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Group identifier |
| `members` | list[string] | List of member IDs (can be user IDs or group IDs) |
| `memberids` | list[string] | Resolved member IDs (if available) |
| `signatures` | list[string] | Signatures |
| `writers` | list[string] | Writers |
| `readers` | list[string] | Readers |
| `nonreaders` | list[string] | Non-readers (explicit exclusions) |
| `tcdate` | int | Creation timestamp |
| `tmdate` | int | Last modification timestamp |

**Output example:**

```json
{
  "id": "ICLR.cc/2024/Conference/Reviewers",
  "members": ["~Reviewer1", "~Reviewer2", "~Reviewer3"],
  "signatures": ["ICLR.cc/2024/Conference"],
  "writers": ["ICLR.cc/2024/Conference"],
  "readers": ["everyone"],
  "tcdate": 1695000000000,
  "tmdate": 1696000000000
}
```

**Tip:** Use this function to get the member list of a reviewer committee or
program committee, then pass individual member IDs to
`search_notes_by_group` or use them for other lookups.

--------------------------------------------------------------------------------

## Bulk Workflow Recipes

**Complete workflow: Search a venue, then get review details for a paper:**

```bash
# Step 1: List available venues
uv run scripts/openreview_api.py ./venues.json list_venues --limit 10

# Step 2: Get submissions for a venue
uv run scripts/openreview_api.py ./submissions.json get_venue_notes "ICLR.cc/2024/Conference" --stage "Submission" --limit 5

# Step 3: Get first submission's forum ID and fetch the full thread
FIRST_FORUM=$(cat ./submissions.json | jq -r '.notes[0].forum // empty')
uv run scripts/openreview_api.py ./thread.json get_notes_by_forum "$FIRST_FORUM"

# Step 4: Extract reviews from the thread
cat ./thread.json | jq '[.notes[] | select(.content.review != null) | {id, review: .content.review, rating: .content.rating}]'
```

**Discover venue structure:**

```bash
# Get venue info
uv run scripts/openreview_api.py ./venue.json get_venue "ICLR.cc/2024/Conference"

# Get venue groups
uv run scripts/openreview_api.py ./groups.json get_venue_groups "ICLR.cc/2024/Conference"

# Get notes from reviewers group
uv run scripts/openreview_api.py ./reviewer_notes.json search_notes_by_group "ICLR.cc/2024/Conference/Reviewers" --limit 20
```
