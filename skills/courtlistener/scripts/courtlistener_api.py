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

r"""CourtListener Legal Research API CLI.

Provides command-line access to the CourtListener REST API v4.
Outputs JSON to the specified output file; all diagnostics go to stderr.

Usage:
  uv run courtlistener_api.py search_results.json \
    search_opinions "free speech" --court ca1 --limit 5
  uv run courtlistener_api.py opinion_12345.json \
    get_opinion_by_id 12345
  uv run courtlistener_api.py courts_list.json \
    list_courts
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

COURTLISTENER_API_BASE = "https://www.courtlistener.com/api/rest/v4"
COURTLISTENER_API_KEY_ENV = "COURTLISTENER_API_KEY"

_CLIENT = None


def get_client():
  """Returns the lazily initialized CourtListener HttpClient."""
  global _CLIENT
  if _CLIENT is None:
    qps = 5  # 5000 req/day ~= 0.058 req/sec; 5 qps is plenty safe
    _CLIENT = http_client.HttpClient(COURTLISTENER_API_BASE, qps=qps)
  return _CLIENT


_MAX_JSON_ERROR_SNIPPET_LENGTH = 500


def _headers():
  """Returns authorization headers from environment."""
  api_key = os.environ.get(COURTLISTENER_API_KEY_ENV)
  if api_key:
    return {"Authorization": f"Token {api_key}"}
  return {}


def _get(url, params=None):
  """GET request with retry logic, rate limiting, and auth headers."""
  client = get_client()
  headers = _headers()
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


def _paginated_get(url, params=None, limit=10):
  """GET with pagination support via CourtListener 'page' / 'next' links.

  CourtListener paginates results using 'next' URLs in the response.
  This fetches up to `limit` results across pages.
  """
  client = get_client()
  headers = _headers()
  all_results = []
  current_url = url
  if params:
    current_url = current_url + "?" + urllib.parse.urlencode(params)

  while current_url and len(all_results) < limit:
    try:
      data = client.fetch_json(current_url, headers=headers)
    except http_client.HttpError as e:
      return {
          "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
          "endpoint": current_url.split("?")[0],
      }
    except json.JSONDecodeError as e:
      body_snippet = e.doc
      if len(body_snippet) > _MAX_JSON_ERROR_SNIPPET_LENGTH:
        body_snippet = f"{body_snippet[:_MAX_JSON_ERROR_SNIPPET_LENGTH]}..."
      return {
          "error": f"Failed to parse JSON response. Body: {body_snippet}",
          "endpoint": current_url.split("?")[0],
      }

    if isinstance(data, dict) and "error" in data:
      return data

    results = data.get("results", [])
    all_results.extend(results)

    # Next page link
    next_url = data.get("next") if isinstance(data, dict) else None
    current_url = next_url

  return all_results[:limit]


# ---------------------------------------------------------------------------
# Opinions
# ---------------------------------------------------------------------------


def search_opinions(
    query: str,
    court: str = "",
    filed_after: str = "",
    filed_before: str = "",
    limit: int = 10,
) -> list[dict]:
  """Search full-text court opinions on CourtListener.

  Supports free-text and fielded search queries. Results can be filtered by
  court, date range, and number of results.

  Args:
    query: Free-text search query
    court: Court ID abbreviation (e.g. 'ca1', 'scotus') — empty for all courts
    filed_after: Date string (YYYY-MM-DD) to filter results filed after
    filed_before: Date string (YYYY-MM-DD) to filter results filed before
    limit: Maximum number of opinions to return (default 10)

  Returns:
    List of opinion result objects
  """
  params = {"q": query, "type": "o"}  # 'o' = opinions search
  if court:
    params["court"] = court
  if filed_after:
    params["filed_after"] = filed_after
  if filed_before:
    params["filed_before"] = filed_before
  params["page[size]"] = min(limit, 100)

  return _paginated_get(f"{COURTLISTENER_API_BASE}/search/", params, limit=limit)


def get_opinion_by_id(opinion_id: int) -> dict:
  """Get a specific opinion by its numeric ID.

  Args:
    opinion_id: Numeric ID of the opinion

  Returns:
    Dict with opinion metadata
  """
  return _get(f"{COURTLISTENER_API_BASE}/opinions/{opinion_id}/")


# ---------------------------------------------------------------------------
# Citations
# ---------------------------------------------------------------------------


def get_opinion_citations(opinion_id: int) -> list[dict]:
  """Get citations to/from an opinion.

  Returns both citing and cited opinions for the given opinion ID.

  Args:
    opinion_id: Numeric ID of the opinion

  Returns:
    List of citation objects
  """
  return _get(f"{COURTLISTENER_API_BASE}/opinions/{opinion_id}/citations/")

# ---------------------------------------------------------------------------
# Dockets
# ---------------------------------------------------------------------------


def search_dockets(
    query: str,
    court: str = "",
    limit: int = 10,
) -> list[dict]:
  """Search dockets on CourtListener.

  Args:
    query: Free-text search query for docket title / case name
    court: Court ID abbreviation (e.g. 'ca1') — empty for all courts
    limit: Maximum number of dockets to return (default 10)

  Returns:
    List of docket result objects
  """
  params = {"q": query, "type": "d"}  # 'd' = dockets search
  if court:
    params["court"] = court
  params["page[size]"] = min(limit, 100)

  return _paginated_get(f"{COURTLISTENER_API_BASE}/search/", params, limit=limit)


def get_docket_entries(
    docket_id: int,
    limit: int = 50,
) -> list[dict]:
  """Get docket entries for a specific docket.

  Args:
    docket_id: Numeric ID of the docket
    limit: Maximum number of entries to return (default 50)

  Returns:
    List of docket entry objects
  """
  params = {"page[size]": min(limit, 100)}
  return _paginated_get(
      f"{COURTLISTENER_API_BASE}/docket-entries/",
      params={**params, "docket": docket_id},
      limit=limit,
  )


def get_docket_by_case_number(case_number: str, court: str) -> dict:
  """Lookup a docket by case number within a specific court.

  Args:
    case_number: Case number string (e.g. '20-1234')
    court: Court ID abbreviation (e.g. 'ca1')

  Returns:
    Docket metadata dict
  """
  params = {"case_name": case_number, "court": court}
  data = _get(f"{COURTLISTENER_API_BASE}/dockets/", params)
  if isinstance(data, dict) and "error" in data:
    return data
  if isinstance(data, dict) and "results" in data:
    results = data.get("results", [])
    if results:
      return results[0]
    return {"error": "No docket found for this case number and court"}
  return data


# ---------------------------------------------------------------------------
# Courts
# ---------------------------------------------------------------------------


def list_courts() -> list[dict]:
  """List all available courts in CourtListener.

  Returns:
    List of court objects with id, name, type, etc.
  """
  return _get(f"{COURTLISTENER_API_BASE}/courts/")


def search_judges(
    name: str = "",
    court: str = "",
) -> list[dict]:
  """Search for judges/people in CourtListener.

  Args:
    name: Judge name to search for (partial match)
    court: Court ID abbreviation to filter by

  Returns:
    List of person objects
  """
  params = {}
  if name:
    params["name"] = name
  if court:
    params["court"] = court
  data = _get(f"{COURTLISTENER_API_BASE}/people/", params)
  if isinstance(data, dict):
    if "error" in data:
      return data
    return data.get("results", [])
  return data


def get_judge_opinions(
    person_id: int,
    limit: int = 50,
) -> list[dict]:
  """Get opinions authored by a specific judge (person).

  Args:
    person_id: Numeric ID of the judge/person
    limit: Maximum number of opinions to return (default 50)

  Returns:
    List of opinion objects authored by the judge
  """
  params = {"page[size]": min(limit, 100)}
  return _paginated_get(
      f"{COURTLISTENER_API_BASE}/opinions/",
      params={**params, "author": person_id},
      limit=limit,
  )


# ---------------------------------------------------------------------------
# Oral Arguments
# ---------------------------------------------------------------------------


def search_oral_arguments(
    query: str,
    court: str = "",
    date_after: str = "",
    limit: int = 10,
) -> list[dict]:
  """Search oral argument recordings in CourtListener.

  Args:
    query: Free-text search query
    court: Court ID abbreviation (e.g. 'scotus') — empty for all courts
    date_after: Date string (YYYY-MM-DD) to filter arguments after
    limit: Maximum number of results to return (default 10)

  Returns:
    List of oral argument result objects with metadata and download URLs
  """
  params = {"q": query, "type": "oa"}  # 'oa' = oral arguments search
  if court:
    params["court"] = court
  if date_after:
    params["argued_after"] = date_after
  params["page[size]"] = min(limit, 100)

  return _paginated_get(f"{COURTLISTENER_API_BASE}/search/", params, limit=limit)


def get_oral_argument(oa_id: int) -> dict:
  """Get oral argument metadata and download URL by ID.

  Args:
    oa_id: Numeric ID of the oral argument recording

  Returns:
    Dict with oral argument metadata including download URL
  """
  return _get(f"{COURTLISTENER_API_BASE}/oral-arguments/{oa_id}/")


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_opinions,
        get_opinion_by_id,
        get_opinion_citations,
        search_dockets,
        get_docket_entries,
        get_docket_by_case_number,
        list_courts,
        search_judges,
        get_judge_opinions,
        search_oral_arguments,
        get_oral_argument,
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
    print("Usage: courtlistener_api.py <output_file> <func> [--flag val]")
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
