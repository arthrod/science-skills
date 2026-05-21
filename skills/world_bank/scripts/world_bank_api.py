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

r"""World Bank API CLI.

Provides command-line access to the World Bank API v2 (free, no auth).
Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run world_bank_api.py ./country_US.json get_country US
  uv run world_bank_api.py ./indicators.json search_indicators "GDP"
  uv run world_bank_api.py ./data.json get_data US NY.GDP.MKTP.CD --start 2010 --end 2020
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

API_BASE = "https://api.worldbank.org/v2/"
DEFAULT_QPS = 5

_CLIENT = None


def get_client():
  """Returns the lazily initialized World Bank API HttpClient."""
  global _CLIENT
  if _CLIENT is None:
    _CLIENT = http_client.HttpClient(API_BASE, qps=DEFAULT_QPS)
  return _CLIENT


def _get(url_path, params=None):
  """GET request with error handling. Automatically adds ?format=json.

  The World Bank API wraps responses as [pagination_metadata, data_array].
  On error, returns a dict with an 'error' key.

  Args:
    url_path: Relative path from API_BASE.
    params: Dict of additional query parameters.

  Returns:
    Parsed JSON data (the actual data array, stripping pagination wrapper).
  """
  if params is None:
    params = {}
  params["format"] = "json"

  full_url = url_path + "?" + urllib.parse.urlencode(params)

  try:
    resp = get_client().fetch(full_url)
    data = resp.json()
  except http_client.HttpError as e:
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": url_path,
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {str(e)}",
        "endpoint": url_path,
    }

  # World Bank API wraps responses as [pagination_metadata, actual_data]
  if isinstance(data, list) and len(data) >= 2:
    return data[1]
  elif isinstance(data, list) and len(data) == 1:
    # Sometimes returns just [pagination_metadata] with no data
    return []
  elif isinstance(data, dict) and "message" in data:
    return {
        "error": data["message"][0]["value"]
        if isinstance(data["message"], list)
        else str(data["message"]),
        "endpoint": url_path,
    }
  return data


# ---------------------------------------------------------------------------
# Countries & Indicators
# ---------------------------------------------------------------------------


def get_country(country_code: str) -> list[dict]:
  """Returns metadata for a single country.

  Args:
    country_code: ISO 3166-1 alpha-2/3 or numeric country code (e.g. "US",
      "GBR").

  Returns:
    List with one dict containing country metadata (name, region, capital,
    income level, etc.) or an error dict.
  """
  return _get(f"country/{urllib.parse.quote(country_code)}")


def search_countries(query: str, limit: int = 50) -> list[dict]:
  """Searches countries by name.

  Uses the World Bank country search endpoint which supports partial
  matching on country name.

  Args:
    query: Search term (country name or partial name).
    limit: Maximum results to return (default 50).

  Returns:
    List of matching country metadata dicts.
  """
  return _get("country", {"search": query, "per_page": limit})


def search_indicators(query: str, topic: int = 0, limit: int = 50) -> list[dict]:
  """Searches available indicators by keyword.

  Args:
    query: Search term for indicator name or description.
    topic: Optional topic ID to filter by (default 0 means no filter).
    limit: Maximum results to return (default 50).

  Returns:
    List of matching indicator metadata dicts.
  """
  params = {"search": query, "per_page": limit}
  if topic:
    params["topic"] = topic
  return _get("indicator", params)


def get_indicator(indicator_id: str) -> list[dict]:
  """Returns metadata for a single indicator.

  Args:
    indicator_id: Indicator ID (e.g. "NY.GDP.MKTP.CD", "SP.POP.TOTL").

  Returns:
    List with one dict containing indicator metadata.
  """
  return _get(f"indicator/{urllib.parse.quote(indicator_id)}")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


def get_data(
    country_code: str,
    indicator_id: str,
    start: str = "",
    end: str = "",
) -> list[dict]:
  """Returns time series data for one country and indicator.

  Args:
    country_code: ISO country code (e.g. "US", "GBR", "WLD" for world).
    indicator_id: Indicator ID (e.g. "NY.GDP.MKTP.CD").
    start: Start year (e.g. "2010"). Empty string means no lower bound.
    end: End year (e.g. "2020"). Empty string means no upper bound.

  Returns:
    List of yearly data points with value, year, and metadata.
  """
  params = {"per_page": 100}
  if start or end:
    params["date"] = f"{start}:{end}" if end else start
  return _get(
      f"country/{urllib.parse.quote(country_code)}/indicator/{urllib.parse.quote(indicator_id)}",
      params,
  )


def get_data_by_countries(
    countries: list[str],
    indicator_id: str,
    start: str = "",
    end: str = "",
) -> list[dict]:
  """Returns time series data for multiple countries and one indicator.

  Countries are joined with semicolons in the API request path.

  Args:
    countries: List of ISO country codes (e.g. ["US", "GBR"]). Passed as
      comma-separated from CLI.
    indicator_id: Indicator ID.
    start: Start year. Empty string means no lower bound.
    end: End year. Empty string means no upper bound.

  Returns:
    List of yearly data points across all specified countries.
  """
  params = {"per_page": 1000}
  if start or end:
    params["date"] = f"{start}:{end}" if end else start

  countries_str = ";".join(countries)
  return _get(
      f"country/{urllib.parse.quote(countries_str)}/indicator/{urllib.parse.quote(indicator_id)}",
      params,
  )


def get_all_countries_data(indicator_id: str, year: str) -> list[dict]:
  """Returns data for ALL countries for one indicator in a given year.

  Useful for cross-country comparisons of a single metric.

  Args:
    indicator_id: Indicator ID.
    year: Year (e.g. "2020").

  Returns:
    List of data points for all available countries in that year.
  """
  return _get(
      f"country/all/indicator/{urllib.parse.quote(indicator_id)}",
      {"date": year, "per_page": 500},
  )


# ---------------------------------------------------------------------------
# Topics & Bulk
# ---------------------------------------------------------------------------


def list_topics(limit: int = 50) -> list[dict]:
  """Lists available development topics.

  Args:
    limit: Maximum topics to return (default 50).

  Returns:
    List of topic metadata dicts with id and value.
  """
  return _get("topic", {"per_page": limit})


def get_topic(topic_id: int) -> list[dict]:
  """Returns details for a single topic.

  Args:
    topic_id: Topic ID (integer, e.g. 1 for Economic Policy & Debt).

  Returns:
    List with one dict containing topic details.
  """
  return _get(f"topic/{topic_id}")


def get_country_indicators(country_code: str, limit: int = 50) -> list[dict]:
  """Lists all available indicators for a given country.

  Args:
    country_code: ISO country code.
    limit: Maximum indicators to return (default 50).

  Returns:
    List of indicator metadata dicts available for that country.
  """
  return _get(
      f"country/{urllib.parse.quote(country_code)}/indicator",
      {"per_page": limit},
  )


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        get_country,
        search_countries,
        search_indicators,
        get_indicator,
        get_data,
        get_data_by_countries,
        get_all_countries_data,
        list_topics,
        get_topic,
        get_country_indicators,
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
    print("Usage: world_bank_api.py <output_file> <func> [--flag val]")
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
