# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""OpenReview API CLI.

Provides command-line access to the OpenReview REST API.
Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run openreview_api.py search_results.json \
    search_notes "transformer" --limit 5
  uv run openreview_api.py note.json \
    get_note "S3ff6d1234567890abcdef1234567890ab"
  uv run openreview_api.py thread.json \
    get_notes_by_forum "S3ff6d1234567890abcdef1234567890ab"
"""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "science-skills-common",
#   "python-dotenv",
# ]
# [tool.uv.sources]
# science-skills-common = { path = "../../science_skills_common" }
# ///

import inspect
import json
import os
import sys
import urllib.parse

import dotenv
from science_skills.science_skills_common import http_client

OPENREVIEW_BASE = "https://api.openreview.net"

_CLIENT = None


def get_client():
  """Returns the lazily initialized OpenReview HttpClient."""
  global _CLIENT
  if _CLIENT is None:
    _CLIENT = http_client.HttpClient(OPENREVIEW_BASE, qps=2)
  return _CLIENT


_MAX_JSON_ERROR_SNIPPET_LENGTH = 500


def _auth_headers():
  """Returns authorization headers if an API key is set in the environment."""
  api_key = os.environ.get("OPENREVIEW_API_KEY")
  if api_key:
    return {"Authorization": f"Bearer {api_key}"}
  return {}


def _get(url, params=None):
  """GET request with retry logic and rate limiting."""
  client = get_client()
  headers = _auth_headers()

  if params:
    url = url + "?" + urllib.parse.urlencode(params)

  try:
    return client.fetch_json(url, headers=headers)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {
          "error": "Record not found (HTTP 404).",
          "endpoint": url.split("?")[0],
      }
    elif e.status_code == 401:
      return {
          "error": "Authentication failed (HTTP 401). Check your OPENREVIEW_API_KEY.",
          "endpoint": url.split("?")[0],
      }
    else:
      return {
          "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
          "endpoint": url.split("?")[0],
      }
  except json.JSONDecodeError as e:
    body_snippet = e.doc
    if len(body_snippet) > _MAX_JSON_ERROR_SNIPPET_LENGTH:
      body_snippet = f"{body_snippet[:_MAX_JSON_ERROR_SNIPPET_LENGTH]}..."
    return {
        "error": f"Failed to parse JSON response. Body: {body_snippet}",
        "endpoint": url.split("?")[0],
    }


# ---------------------------------------------------------------------------
# Search Functions
# ---------------------------------------------------------------------------


def search_notes(
    query: str,
    venue: str = "",
    limit: int = 20,
) -> dict:
  """Searches OpenReview notes by query text.

  Searches the OpenReview notes index for papers, reviews, and comments
  matching the given query string. Optionally filter by venue ID.

  Args:
    query: Free-text search query
    venue: Optional venue ID to restrict results
    limit: Maximum number of notes to return (default 20)

  Returns:
    Dict with notes list and count
  """
  params = {"term": query, "limit": limit}
  if venue:
    params["venue"] = venue

  data = _get("/notes/search", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def get_note(
    note_id: str,
) -> dict:
  """Retrieves full details of a single note.

  Fetches the complete note object including all content fields (title,
  abstract, authors, reviews, comments, decisions, etc., depending on
  the note type and access permissions).

  Args:
    note_id: The note ID to retrieve

  Returns:
    Dict with note details
  """
  params = {"id": note_id}
  data = _get("/notes", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    notes = data.get("notes", [])
    if notes:
      return notes[0]
    return {"error": "Note not found", "endpoint": "/notes"}
  except (KeyError, TypeError, IndexError):
    return {"error": "Unexpected notes response structure", "endpoint": "/notes"}


def get_venue(
    venue_id: str,
) -> dict:
  """Retrieves metadata for a conference/venue.

  Fetches venue details including name, short name, and other metadata.

  Args:
    venue_id: The venue ID (e.g. 'ICLR.cc/2024/Conference')

  Returns:
    Dict with venue metadata
  """
  params = {"id": venue_id}
  data = _get("/venues", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    venues = data.get("venues", [])
    if venues:
      return venues[0]
    return {"error": "Venue not found", "endpoint": "/venues"}
  except (KeyError, TypeError, IndexError):
    return {"error": "Unexpected venues response structure", "endpoint": "/venues"}


# ---------------------------------------------------------------------------
# Venue Functions
# ---------------------------------------------------------------------------


def get_venue_notes(
    venue_id: str,
    stage: str = "",
    limit: int = 20,
) -> dict:
  """Gets notes (papers/reviews) by venue and submission stage.

  Fetches notes associated with a specific venue, optionally filtered by
  submission stage (e.g. 'Submission', 'Decision', 'Withdrawal').

  Args:
    venue_id: The venue ID (e.g. 'ICLR.cc/2024/Conference')
    stage: Optional submission stage filter
    limit: Maximum number of notes to return (default 20)

  Returns:
    Dict with notes list and count
  """
  params = {"limit": limit}
  if stage:
    params["stage"] = stage

  url = f"/venues/{urllib.parse.quote(venue_id, safe='')}/notes"
  data = _get(url, params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def get_venue_groups(
    venue_id: str,
) -> dict:
  """Gets the groups/committees associated with a venue.

  Fetches all groups (e.g. reviewers, area chairs, program committee)
  associated with the specified venue.

  Args:
    venue_id: The venue ID (e.g. 'ICLR.cc/2024/Conference')

  Returns:
    Dict with groups list
  """
  params = {"id": venue_id}
  data = _get("/groups", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def list_venues(
    limit: int = 50,
) -> dict:
  """Lists available venues/conferences.

  Returns a list of all venues/conferences in the OpenReview system.

  Args:
    limit: Maximum number of venues to return (default 50)

  Returns:
    Dict with venues list
  """
  params = {"limit": limit}
  data = _get("/venues", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


# ---------------------------------------------------------------------------
# Bulk Functions
# ---------------------------------------------------------------------------


def search_notes_by_group(
    group_id: str,
    limit: int = 50,
) -> dict:
  """Gets notes (papers/reviews) by a specific group.

  Fetches all notes authored by members of the specified group.

  Args:
    group_id: The group ID (e.g. 'ICLR.cc/2024/Conference/Reviewers')
    limit: Maximum number of notes to return (default 50)

  Returns:
    Dict with notes list and count
  """
  params = {"id": group_id, "limit": limit}
  data = _get("/notes", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def get_notes_by_forum(
    forum_id: str,
) -> dict:
  """Gets all notes in a forum thread.

  Fetches all notes belonging to the same forum thread, which includes the
  original paper submission, all reviews, meta-reviews, author responses,
  decision notifications, and comments.

  Args:
    forum_id: The forum ID (note ID of the original paper submission)

  Returns:
    Dict with all notes in the forum sorted by date
  """
  params = {"forum": forum_id}
  data = _get("/notes", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def get_group(
    group_id: str,
) -> dict:
  """Gets information about a specific group.

  Fetches group metadata including members, parent group, and permissions.

  Args:
    group_id: The group ID (e.g. 'ICLR.cc/2024/Conference/Reviewers')

  Returns:
    Dict with group details
  """
  params = {"id": group_id}
  data = _get("/groups", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    groups = data.get("groups", [])
    if groups:
      return groups[0]
    return {"error": "Group not found", "endpoint": "/groups"}
  except (KeyError, TypeError, IndexError):
    return {
        "error": "Unexpected groups response structure",
        "endpoint": "/groups",
    }


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_notes,
        get_note,
        get_venue,
        get_venue_notes,
        get_venue_groups,
        list_venues,
        search_notes_by_group,
        get_notes_by_forum,
        get_group,
    ]
}


def _is_list_type(annotation):
  origin = getattr(annotation, "__origin__", None)
  return origin is list


def _coerce_arg(value: str, annotation):
  if _is_list_type(annotation):
    return value.split(",")
  if annotation is int:
    return int(value)
  return value


def main():
  dotenv.load_dotenv(os.path.expanduser("~/.env"))
  if len(sys.argv) < 3:
    print("Usage: openreview_api.py <output_file> <func> [--flag val]")
    print(f"Available: {', '.join(FUNCTIONS.keys())}")
    sys.exit(1)

  output_file = sys.argv[1]
  func_name = sys.argv[2]
  if func_name not in FUNCTIONS:
    print(f"Error: Unknown function: {func_name}")
    sys.exit(1)

  if os.path.exists(output_file):
    print(f"Error: Output file {output_file} already exists")
    sys.exit(1)

  fn = FUNCTIONS[func_name]
  sig = inspect.signature(fn)

  positional = []
  flags = {}
  raw_args = sys.argv[3:]
  i = 0
  while i < len(raw_args):
    if raw_args[i].startswith("--"):
      key = raw_args[i][2:]
      if i + 1 < len(raw_args):
        flags[key] = raw_args[i + 1]
        i += 2
      else:
        print(f"Error: Missing value for flag --{key}")
        sys.exit(1)
    else:
      positional.append(raw_args[i])
      i += 1

  kwargs = {}
  pos_idx = 0
  for name, param in sig.parameters.items():
    if name in flags:
      kwargs[name] = _coerce_arg(flags[name], param.annotation)
    elif pos_idx < len(positional):
      kwargs[name] = _coerce_arg(positional[pos_idx], param.annotation)
      pos_idx += 1
    elif param.default is not inspect.Parameter.empty:
      kwargs[name] = param.default
    else:
      print(f"Error: Missing required argument: {name}")
      sys.exit(1)

  try:
    result = fn(**kwargs)
  except Exception as e:
    print(f"Internal error in {func_name}: {e}")
    sys.exit(2)

  if isinstance(result, dict) and "error" in result:
    msg = result["error"]
    endpoint = result.get("endpoint", "")
    if endpoint:
      print(f"API error ({endpoint}): {msg}")
    else:
      print(f"API error: {msg}")
    sys.exit(1)

  with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
    print(file=f)

  if isinstance(result, list):
    print(f"API call OK: {len(result)} results written to {output_file}")
  elif isinstance(result, dict):
    keys = ", ".join(sorted(result.keys()))
    print(f"API call OK: result ({keys}) written to {output_file}")
  else:
    print(f"API call OK: result written to {output_file}")


if __name__ == "__main__":
  main()
