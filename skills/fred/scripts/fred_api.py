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

r"""FRED API CLI.

Provides command-line access to the Federal Reserve Economic Data API.
Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run fred_api.py search_results.json \
    search_series "GDP" --limit 5
  uv run fred_api.py gdp_observations.json \
    get_series_observations "GDP" --start "2020-01-01"
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

FRED_BASE = "https://api.stlouisfed.org/fred"

_FRED_CLIENT = None


def get_fred_client():
  """Returns the lazily initialized FRED HttpClient.

  FRED rate limit is 120 requests per minute.
  """
  global _FRED_CLIENT
  if _FRED_CLIENT is None:
    _FRED_CLIENT = http_client.HttpClient(FRED_BASE, qps=120)
  return _FRED_CLIENT


_MAX_JSON_ERROR_SNIPPET_LENGTH = 500


def _env_params():
  """Returns a dictionary of parameters from the environment.

  Every FRED API call requires api_key and file_type=json.
  """
  params = {"file_type": "json"}
  api_key = os.environ.get("FRED_API_KEY")
  if api_key:
    params["api_key"] = api_key
  return params


def _get(endpoint, params=None):
  """GET request with retry logic and rate limiting."""
  url = f"{FRED_BASE}/{endpoint}"
  if params:
    url = url + "?" + urllib.parse.urlencode(params)

  try:
    return get_fred_client().fetch_json(url)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {
          "error": "Record not found (HTTP 404).",
          "endpoint": endpoint,
      }
    else:
      return {
          "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
          "endpoint": endpoint,
      }
  except json.JSONDecodeError as e:
    body_snippet = e.doc
    if len(body_snippet) > _MAX_JSON_ERROR_SNIPPET_LENGTH:
      body_snippet = f"{body_snippet[:_MAX_JSON_ERROR_SNIPPET_LENGTH]}..."
    return {
        "error": f"Failed to parse JSON response. Body: {body_snippet}",
        "endpoint": endpoint,
    }


# -------------------------------------------------------------------------
# Search functions
# -------------------------------------------------------------------------


def search_series(
    query: str,
    search_type: str = "full_text",
    limit: int = 25,
) -> list[dict]:
  """Searches for FRED series matching a free-text query.

  The FRED series search endpoint returns a list of series that match the
  search text. Results include series ID, title, units, frequency, and
  seasonal adjustment.

  Args:
    query: Free-text search string for economic series
    search_type: 'full_text' (default) or 'series_id'
    limit: Maximum number of series to return (max 1000)

  Returns:
    List of series dicts with id, title, units, frequency, and other metadata
  """
  params = _env_params() | {
      "search_text": query,
      "search_type": search_type,
      "limit": limit,
  }
  data = _get("series/search", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    series_list = data.get("seriess", [])
    if isinstance(series_list, dict):
      # FRED returns a dict when there's only one result
      return [series_list]
    return series_list
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected series/search response structure",
        "endpoint": "series/search",
    }


def get_series_info(
    series_id: str,
) -> dict:
  """Retrieves metadata for a specific FRED series.

  Returns detailed information about a single economic series including
  its title, units, frequency, seasonal adjustment, notes, and date range.

  Args:
    series_id: FRED series ID (e.g. 'GDP', 'UNRATE', 'FEDFUNDS')

  Returns:
    Dict with series metadata (id, title, units, frequency, notes, etc.)
  """
  params = _env_params() | {
      "series_id": series_id,
  }
  data = _get("series", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    series_data = data.get("seriess", [])
    if isinstance(series_data, list) and series_data:
      return series_data[0]
    if isinstance(series_data, dict):
      return series_data
    return {"error": "Series not found", "series_id": series_id}
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected series response structure",
        "endpoint": "series",
    }


# -------------------------------------------------------------------------
# Data functions
# -------------------------------------------------------------------------


def get_series_observations(
    series_id: str,
    start: str = "",
    end: str = "",
    frequency: str = "",
) -> dict:
  """Retrieves time series observations for a FRED series.

  Returns the observation values (dates and values) for the specified
  series. Optionally filtered by start/end date and frequency aggregation.

  Args:
    series_id: FRED series ID (e.g. 'GDP', 'UNRATE', 'FEDFUNDS')
    start: Start date in 'YYYY-MM-DD' format
    end: End date in 'YYYY-MM-DD' format
    frequency: Aggregation frequency — 'd' (daily), 'w' (weekly),
      'bw' (biweekly), 'm' (monthly), 'q' (quarterly), 'sa' (semiannual),
      'a' (annual)

  Returns:
    Dict with series metadata and observations list
  """
  params = _env_params() | {
      "series_id": series_id,
  }
  if start:
    params["observation_start"] = start
  if end:
    params["observation_end"] = end
  if frequency:
    params["frequency"] = frequency

  data = _get("series/observations", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def get_series_categories(
    series_id: str,
) -> list[dict]:
  """Retrieves category assignments for a FRED series.

  Returns the categories (e.g. 'National Accounts', 'Population') that a
  series belongs to.

  Args:
    series_id: FRED series ID

  Returns:
    List of category dicts with id, name, and parent_id
  """
  params = _env_params() | {
      "series_id": series_id,
  }
  data = _get("series/categories", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    cats = data.get("categories", [])
    if isinstance(cats, dict):
      return [cats]
    return cats
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected series/categories response structure",
        "endpoint": "series/categories",
    }


def get_series_release(
    series_id: str,
) -> dict:
  """Retrieves the release for a FRED series.

  Returns information about the economic release that a series belongs to
  (e.g. 'Gross Domestic Product', 'Employment Situation').

  Args:
    series_id: FRED series ID

  Returns:
    Dict with release info (id, name, press_release, link, etc.)
  """
  params = _env_params() | {
      "series_id": series_id,
  }
  data = _get("series/release", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    release_data = data.get("releases", [])
    if isinstance(release_data, list) and release_data:
      return release_data[0]
    if isinstance(release_data, dict):
      return release_data
    return {"error": "Release not found", "series_id": series_id}
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected series/release response structure",
        "endpoint": "series/release",
    }


def get_series_tags(
    series_id: str,
) -> list[dict]:
  """Retrieves tags for a FRED series.

  Tags describe attributes of the series (e.g. 'usa', 'annual', 'gdp').

  Args:
    series_id: FRED series ID

  Returns:
    List of tag dicts with name, group_id, and notes
  """
  params = _env_params() | {
      "series_id": series_id,
  }
  data = _get("series/tags", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    tags = data.get("tags", [])
    if isinstance(tags, dict):
      return [tags]
    return tags
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected series/tags response structure",
        "endpoint": "series/tags",
    }


# -------------------------------------------------------------------------
# Categories & Releases
# -------------------------------------------------------------------------


def get_category(
    category_id: int,
) -> dict:
  """Retrieves category metadata and child categories.

  FRED categories form a tree. This returns the specified category's details
  and its immediate children. Root category is 0.

  Args:
    category_id: Category ID (integer, e.g. 0 for root, 1 for Output)

  Returns:
    Dict with categories list (parent + children) or error
  """
  params = _env_params() | {
      "category_id": category_id,
  }
  data = _get("category", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    cats = data.get("categories", [])
    if isinstance(cats, dict):
      return [cats]
    return cats
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected category response structure",
        "endpoint": "category",
    }


def get_category_series(
    category_id: int,
    limit: int = 25,
) -> list[dict]:
  """Retrieves series within a FRED category.

  Returns all series belonging to a specific category.

  Args:
    category_id: Category ID (integer)
    limit: Maximum number of series to return (max 1000)

  Returns:
    List of series dicts
  """
  params = _env_params() | {
      "category_id": category_id,
      "limit": limit,
  }
  data = _get("category/series", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    series_list = data.get("seriess", [])
    if isinstance(series_list, dict):
      return [series_list]
    return series_list
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected category/series response structure",
        "endpoint": "category/series",
    }


def get_releases(
    limit: int = 25,
) -> list[dict]:
  """Retrieves all economic releases.

  Returns a list of all FRED releases (e.g. 'Gross Domestic Product',
  'Consumer Price Index'), which are groups of related series.

  Args:
    limit: Maximum number of releases to return (max 1000)

  Returns:
    List of release dicts with id, name, press_release, link, etc.
  """
  params = _env_params() | {
      "limit": limit,
  }
  data = _get("releases", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    releases = data.get("releases", [])
    if isinstance(releases, dict):
      return [releases]
    return releases
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected releases response structure",
        "endpoint": "releases",
    }


def get_release(
    release_id: int,
) -> dict:
  """Retrieves a specific economic release.

  Returns metadata about a single release, including its name, link,
  press release URL, and notes.

  Args:
    release_id: Release ID (integer)

  Returns:
    Dict with release metadata
  """
  params = _env_params() | {
      "release_id": release_id,
  }
  data = _get("release", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    releases = data.get("releases", [])
    if isinstance(releases, list) and releases:
      return releases[0]
    if isinstance(releases, dict):
      return releases
    return {"error": "Release not found", "release_id": release_id}
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected release response structure",
        "endpoint": "release",
    }


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_series,
        get_series_info,
        get_series_observations,
        get_series_categories,
        get_series_release,
        get_series_tags,
        get_category,
        get_category_series,
        get_releases,
        get_release,
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
    print("Usage: fred_api.py <output_file> <func> [--flag val]")
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
    print(f"API call OK: {len(result)} results json written to {output_file}")
  elif isinstance(result, dict):
    keys = ", ".join(sorted(result.keys()))
    print(f"API call OK: result ({keys}) json written to {output_file}")
  else:
    print(f"API call OK: result json written to {output_file}")


if __name__ == "__main__":
  main()
