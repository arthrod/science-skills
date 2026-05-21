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

r"""UK Legislation API CLI.

Provides command-line access to the legislation.gov.uk API.
Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run legislation_api.py search_results.json \
    search_legislation "climate change" --limit 5
  uv run legislation_api.py ukpga_2023_1.json \
    get_legislation "ukpga/2023/1"
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

LEGISLATION_BASE = "https://www.legislation.gov.uk"

_LEGISLATION_CLIENT = None


def get_legislation_client():
  """Returns the lazily initialized legislation.gov.uk HttpClient."""
  global _LEGISLATION_CLIENT
  if _LEGISLATION_CLIENT is None:
    _LEGISLATION_CLIENT = http_client.HttpClient(
        LEGISLATION_BASE,
        qps=10,
        referer_skill="legislation-gov-uk",
    )
  return _LEGISLATION_CLIENT


_MAX_JSON_ERROR_SNIPPET_LENGTH = 500


def _get(url, params=None, *, raw=False):
  """GET request with retry logic and rate limiting for legislation.gov.uk."""
  client = get_legislation_client()

  full_url = url
  if params:
    separator = "&" if "?" in url else "?"
    full_url = url + separator + urllib.parse.urlencode(params)

  try:
    resp = client.fetch(full_url, headers={"Accept": "application/json"})
    if raw:
      return resp.text
    return resp.json()
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {
          "error": "Record not found (HTTP 404).",
          "endpoint": full_url,
      }
    else:
      return {
          "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
          "endpoint": full_url,
      }
  except json.JSONDecodeError as e:
    body_snippet = e.doc
    if len(body_snippet) > _MAX_JSON_ERROR_SNIPPET_LENGTH:
      body_snippet = f"{body_snippet[:_MAX_JSON_ERROR_SNIPPET_LENGTH]}..."
    return {
        "error": f"Failed to parse JSON response. Body: {body_snippet}",
        "endpoint": full_url,
    }


def search_legislation(
    query: str,
    year: str = "",
    type: str = "",
    limit: int = 20,
) -> dict:
  """Search UK legislation by keyword query.

  Uses the legislation.gov.uk search endpoint. Results include titles, years,
  legislation types, and IDs that can be passed to get_legislation for full
  text retrieval.

  Args:
    query: Free-text search query.
    year: Optional year filter (e.g. "2023").
    type: Optional legislation type filter (e.g. "Acts", "SI").
    limit: Maximum results to return (default: 20).

  Returns:
    Dict with total_results and results list.
  """
  params = {"search": query}
  if year:
    params["year"] = year
  if type:
    params["type"] = type

  data = _get(f"{LEGISLATION_BASE}/api/v1/legislation", params)

  if isinstance(data, dict) and "error" in data:
    return data

  results = data.get("results", [])[:limit] if isinstance(data, dict) else []
  total = data.get("total_results", len(results)) if isinstance(data, dict) else len(results)

  return {
      "total_results": total,
      "results": results,
  }


def get_legislation(legislation_id: str) -> dict:
  """Retrieve full text of a specific piece of legislation.

  The legislation_id should be in the URL path format used by
  legislation.gov.uk (e.g. "ukpga/2023/1" for the Finance Act 2023).

  Args:
    legislation_id: Legislation identifier in path format (e.g. "ukpga/2023/1").

  Returns:
    Dict with legislation metadata and full text.
  """
  id_clean = legislation_id.strip("/")
  data = _get(f"{LEGISLATION_BASE}/id/{id_clean}")

  if isinstance(data, dict) and "error" in data:
    return data

  return data


def get_legislation_types(limit: int = 50) -> dict:
  """List available legislation types.

  Returns the list of legislation types available on legislation.gov.uk,
  such as "Acts", "Statutory Instruments", "Scottish Statutory Instruments",
  etc.

  Args:
    limit: Maximum types to return (default: 50).

  Returns:
    Dict with a types list.
  """
  data = _get(f"{LEGISLATION_BASE}/types")

  if isinstance(data, dict) and "error" in data:
    return data

  types = data.get("types", data) if isinstance(data, dict) else data
  if isinstance(types, list):
    types = types[:limit]

  return {"types": types, "total": len(types) if isinstance(types, list) else 0}


def get_legislation_by_year(
    year: str,
    type: str = "",
    limit: int = 20,
) -> dict:
  """Retrieve all legislation from a given year.

  Args:
    year: The year to query (e.g. "2023").
    type: Optional type filter (e.g. "Acts", "SI").
    limit: Maximum results to return (default: 20).

  Returns:
    Dict with total_results and results list.
  """
  params = {"year": year}
  if type:
    params["type"] = type

  data = _get(f"{LEGISLATION_BASE}/api/v1/legislation", params)

  if isinstance(data, dict) and "error" in data:
    return data

  results = data.get("results", [])[:limit] if isinstance(data, dict) else []
  total = data.get("total_results", len(results)) if isinstance(data, dict) else len(results)

  return {
      "total_results": total,
      "results": results,
  }


def get_legislation_changes(legislation_id: str) -> dict:
  """Retrieve amendments and changes for a piece of legislation over time.

  Args:
    legislation_id: Legislation identifier in path format (e.g. "ukpga/2023/1").

  Returns:
    Dict with changes data including amendments and timelines.
  """
  id_clean = legislation_id.strip("/")
  data = _get(f"{LEGISLATION_BASE}/id/{id_clean}/changes")

  if isinstance(data, dict) and "error" in data:
    return data

  return data


def get_legislation_versions(legislation_id: str) -> dict:
  """Retrieve available versions (historical and current) of legislation.

  Args:
    legislation_id: Legislation identifier in path format (e.g. "ukpga/2023/1").

  Returns:
    Dict with version data including dates and status.
  """
  id_clean = legislation_id.strip("/")
  data = _get(f"{LEGISLATION_BASE}/id/{id_clean}/versions")

  if isinstance(data, dict) and "error" in data:
    return data

  return data


def get_legislation_by_type(
    type: str,
    year: str = "",
    limit: int = 20,
) -> dict:
  """Filter legislation by type.

  Args:
    type: Legislation type (e.g. "Acts", "SI", "SSI", "WSI").
    year: Optional year filter (e.g. "2023").
    limit: Maximum results to return (default: 20).

  Returns:
    Dict with total_results and results list.
  """
  params = {"type": type}
  if year:
    params["year"] = year

  data = _get(f"{LEGISLATION_BASE}/api/v1/legislation", params)

  if isinstance(data, dict) and "error" in data:
    return data

  results = data.get("results", [])[:limit] if isinstance(data, dict) else []
  total = data.get("total_results", len(results)) if isinstance(data, dict) else len(results)

  return {
      "total_results": total,
      "results": results,
  }


def get_legislation_by_agency(
    agency: str,
    limit: int = 20,
) -> dict:
  """Retrieve legislation by UK government department or agency.

  Args:
    agency: Agency name (e.g. "Department for Environment, Food and Rural Affairs").
    limit: Maximum results to return (default: 20).

  Returns:
    Dict with total_results and results list.
  """
  params = {"agency": agency}

  data = _get(f"{LEGISLATION_BASE}/api/v1/legislation", params)

  if isinstance(data, dict) and "error" in data:
    return data

  results = data.get("results", [])[:limit] if isinstance(data, dict) else []
  total = data.get("total_results", len(results)) if isinstance(data, dict) else len(results)

  return {
      "total_results": total,
      "results": results,
  }


def search_by_geography(
    geography: str,
    limit: int = 20,
) -> dict:
  """Search legislation by applicable geography.

  Args:
    geography: Geography filter (e.g. "England", "Scotland", "Wales",
      "Northern Ireland", "UK").
    limit: Maximum results to return (default: 20).

  Returns:
    Dict with total_results and results list.
  """
  params = {"geography": geography}

  data = _get(f"{LEGISLATION_BASE}/api/v1/legislation", params)

  if isinstance(data, dict) and "error" in data:
    return data

  results = data.get("results", [])[:limit] if isinstance(data, dict) else []
  total = data.get("total_results", len(results)) if isinstance(data, dict) else len(results)

  return {
      "total_results": total,
      "results": results,
  }


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_legislation,
        get_legislation,
        get_legislation_types,
        get_legislation_by_year,
        get_legislation_changes,
        get_legislation_versions,
        get_legislation_by_type,
        get_legislation_by_agency,
        search_by_geography,
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
    print("Usage: legislation_api.py <output_file> <func> [args...]")
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
