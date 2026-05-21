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

r"""Oyez Supreme Court API CLI.

Provides command-line access to the Oyez.org API for searching and
retrieving U.S. Supreme Court cases, oral arguments, and justice
information. No API key required — the Oyez API is free and public.

Usage:
  uv run scripts/oyez_api.py results.json search_cases "free speech" --limit 10
  uv run scripts/oyez_api.py case.json get_case 12345
  uv run scripts/oyez_api.py docket.json get_case_by_docket "22-1234"
  uv run scripts/oyez_api.py justices.json list_justices
"""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "science-skills-common",
# ]
# [tool.uv.sources]
# science-skills-common = { path = "../../science_skills_common" }
# ///

import inspect
import json
import os
import sys
import urllib.parse

from science_skills.science_skills_common import http_client

OYEZ_BASE = "https://api.oyez.org"

_OYEZ_CLIENT = None

_MAX_JSON_ERROR_SNIPPET_LENGTH = 500


def get_oyez_client():
  """Returns the lazily initialized Oyez HttpClient."""
  global _OYEZ_CLIENT
  if _OYEZ_CLIENT is None:
    _OYEZ_CLIENT = http_client.HttpClient(OYEZ_BASE, qps=5)
  return _OYEZ_CLIENT


def _get(url, params=None):
  """GET request with retry logic and rate limiting."""
  client = get_oyez_client()
  if params:
    url = url + "?" + urllib.parse.urlencode(params)
  try:
    return client.fetch_json(url)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {
          "error": "Record not found (HTTP 404).",
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


def search_cases(query: str, limit: int = 20) -> list[dict]:
  """Search Supreme Court cases by keyword or phrase.

  Searches the Oyez case database using a free-text query. Results are
  paginated; use the limit parameter to control how many cases are returned.

  Args:
    query: Free-text search query (e.g. "free speech", "Miranda", "abortion")
    limit: Maximum number of cases to return (default 20)

  Returns:
    List of case summary dicts, each containing name, href, ID, and term info
  """
  params = {"q": query, "per_page": limit, "page": 1}
  data = _get(f"{OYEZ_BASE}/cases", params)
  if isinstance(data, dict) and "error" in data:
    return data
  if isinstance(data, list):
    return data
  return {"error": "Unexpected API response format", "endpoint": "/cases"}


def get_case(case_id: str) -> dict:
  """Retrieve full details for a specific Supreme Court case.

  Returns case metadata, docket numbers, advocates, lower court rulings,
  and decisions. The case_id is the numeric Oyez ID (e.g. "12345") or UUID.

  Args:
    case_id: Oyez case ID (numeric or UUID)

  Returns:
    Dict with full case details including oral argument links, advocates,
    decisions, and docket information
  """
  data = _get(f"{OYEZ_BASE}/cases/{case_id}")
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def get_case_by_docket(docket_number: str) -> list[dict]:
  """Look up a Supreme Court case by its docket number.

  Docket numbers are formatted like "22-1234" or "20-1234". Returns all
  cases matching the docket number.

  Args:
    docket_number: Docket number string (e.g. "22-1234")

  Returns:
    List of matching case summaries
  """
  params = {"docket_number": docket_number}
  data = _get(f"{OYEZ_BASE}/cases", params)
  if isinstance(data, dict) and "error" in data:
    return data
  if isinstance(data, list):
    return data
  return {"error": "Unexpected API response format", "endpoint": "/cases"}


def get_oral_argument(case_id: str) -> dict:
  """Retrieve the oral argument transcript for a case.

  Returns the full oral argument transcript with timing annotations,
  speaker identifications, and a list of advocates who argued.

  Args:
    case_id: Oyez case ID (numeric or UUID)

  Returns:
    Dict with oral argument transcript data including speakers and sections
  """
  data = _get(f"{OYEZ_BASE}/cases/{case_id}/oral_argument")
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def get_oral_argument_audio(case_id: str) -> list[dict]:
  """Retrieve oral argument audio file URLs for a case.

  Returns a list of audio file metadata including media URLs, file
  formats, and duration information for the oral argument recording.

  Args:
    case_id: Oyez case ID (numeric or UUID)

  Returns:
    List of audio file metadata dicts with media URLs
  """
  data = _get(f"{OYEZ_BASE}/cases/{case_id}/oral_argument_audio")
  if isinstance(data, dict) and "error" in data:
    return data
  if isinstance(data, list):
    return data
  return {
      "error": "Unexpected API response format",
      "endpoint": f"/cases/{case_id}/oral_argument_audio",
  }


def search_oral_arguments_by_term(term: str, limit: int = 50) -> list[dict]:
  """Search oral arguments by Supreme Court term.

  A Supreme Court term runs from October to June and is named by the year
  it starts (e.g. term "2023" covers October 2023 through June 2024).
  Returns all cases and their oral argument data for that term.

  Args:
    term: Supreme Court term year (e.g. "2023")
    limit: Maximum number of results to return (default 50)

  Returns:
    List of case dicts with oral argument data for the specified term
  """
  params = {"term": term, "per_page": limit, "page": 1}
  data = _get(f"{OYEZ_BASE}/cases", params)
  if isinstance(data, dict) and "error" in data:
    return data
  if isinstance(data, list):
    return data
  return {"error": "Unexpected API response format", "endpoint": "/cases"}


def get_justice(justice_name: str) -> dict:
  """Retrieve biography and voting record for a Supreme Court justice.

  Searches for a justice by name and returns their detailed biographical
  information including appointment date, nominating president, and case
  involvement data.

  Args:
    justice_name: Full or partial name of the justice (e.g. "John Roberts",
      "Sotomayor", "Clarence Thomas")

  Returns:
    Dict with justice biography including name, title, appointment details,
    and related case links
  """
  params = {"q": justice_name}
  data = _get(f"{OYEZ_BASE}/people", params)
  if isinstance(data, dict) and "error" in data:
    return data
  if isinstance(data, list) and len(data) > 0:
    person_id = None
    href = data[0].get("href", "")
    if href:
      person_id = href.rstrip("/").split("/")[-1]
    if person_id:
      return get_justice_by_id(person_id)
    return data[0]
  return {"error": f"No justice found matching '{justice_name}'", "endpoint": "/people"}


def get_justice_by_id(person_id: str) -> dict:
  """Retrieve a justice by Oyez person ID.

  Args:
    person_id: Oyez person ID (numeric or UUID)

  Returns:
    Dict with full justice biography
  """
  data = _get(f"{OYEZ_BASE}/people/{person_id}")
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def list_justices() -> list[dict]:
  """List all Supreme Court justices.

  Returns biographical data for every justice who has served on the Supreme
  Court, including those currently serving and retired/deceased justices.

  Args:
    None

  Returns:
    List of justice summary dicts with name, title, and href
  """
  data = _get(f"{OYEZ_BASE}/people")
  if isinstance(data, dict) and "error" in data:
    return data
  if isinstance(data, list):
    return data
  return {"error": "Unexpected API response format", "endpoint": "/people"}


def get_justice_votes(justice_name: str) -> dict:
  """Retrieve the voting record of a Supreme Court justice.

  Searches for a justice by name and returns their detailed profile
  including the cases they participated in and their voting record. This
  wraps get_justice but makes the intent explicit.

  Args:
    justice_name: Full or partial name of the justice

  Returns:
    Dict with justice biography and voting-related data
  """
  return get_justice(justice_name)


def get_cases_by_term(term: str, limit: int = 50) -> list[dict]:
  """Retrieve all cases heard in a specific Supreme Court term.

  A Supreme Court term runs from October to June and is named by the year
  it starts (e.g. term "2023" covers October 2023 through June 2024).
  This is an alias for search_oral_arguments_by_term.

  Args:
    term: Supreme Court term year (e.g. "2023")
    limit: Maximum number of results to return (default 50)

  Returns:
    List of case summary dicts for the specified term
  """
  return search_oral_arguments_by_term(term, limit)


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_cases,
        get_case,
        get_case_by_docket,
        get_oral_argument,
        get_oral_argument_audio,
        search_oral_arguments_by_term,
        get_justice,
        list_justices,
        get_justice_votes,
        get_cases_by_term,
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
  if len(sys.argv) < 3:
    print("Usage: oyez_api.py <output_file> <func> [--flag val]")
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
