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

r"""CrossRef API CLI.

Provides command-line access to the Crossref REST API.
Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run crossref_api.py search_results.json \
    search_works "deep learning" --limit 5
  uv run crossref_api.py work_10.1038_nature12373.json \
    get_work "10.1038/nature12373"
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

CROSSREF_API_BASE = "https://api.crossref.org"

_CLIENT = None


def get_client():
  """Returns the lazily initialized CrossRef HttpClient."""
  global _CLIENT
  if _CLIENT is None:
    _CLIENT = http_client.HttpClient(CROSSREF_API_BASE, qps=50)
  return _CLIENT


_MAX_JSON_ERROR_SNIPPET_LENGTH = 500


def _get(url, params=None):
  """GET request with retry logic and rate limiting."""
  client = get_client()
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


def _env_params():
  """Returns query parameters from environment (mailto)."""
  params = {}
  email = os.environ.get("USER_EMAIL")
  if email:
    params["mailto"] = email
  return params


def _env_headers():
  """Returns HTTP headers from environment (Crossref-Plus-API-Key)."""
  headers = {}
  api_key = os.environ.get("CROSSREF_API_KEY")
  if api_key:
    headers["Crossref-Plus-API-Key"] = api_key
  return headers


def _extract_message(data, field="items"):
  """Extract the message body from a CrossRef API response.

  Wraps single-item responses in a list for consistent output, extracts
  items from paginated responses, and handles error responses uniformly.
  """
  if isinstance(data, dict) and "error" in data:
    return data
  if isinstance(data, dict) and "message" in data:
    msg = data["message"]
    if field and isinstance(msg, dict) and field in msg:
      return msg[field]
    return msg
  return {"error": "Unexpected CrossRef response structure", "endpoint": ""}


def search_works(query: str, filter: str = "", limit: int = 20) -> list[dict]:
  """Search scholarly works on CrossRef by title, author, DOI, etc.

  Supports full CrossRef query syntax. The filter parameter accepts
  comma-separated filter key:value pairs (e.g. 'type:journal-article,
  has-references:t').

  Args:
    query: Free-text or structured query string
    filter: Comma-separated filter key:value pairs (optional)
    limit: Maximum results to return (max 1000)

  Returns:
    List of work objects with title, authors, DOI, etc.
  """
  params = _env_params() | {
      "query": query,
      "rows": limit,
  }
  if filter:
    params["filter"] = filter
  headers = _env_headers()
  try:
    data = get_client().fetch_json(
        "/works",
        params=params if params else None,
    )
    if isinstance(data, dict) and "error" in data:
      return data
    return _extract_message(data, "items")
  except http_client.HttpError as e:
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": "/works",
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": "/works",
    }


def get_work(doi: str) -> dict:
  """Retrieve full metadata for a scholarly work by its DOI.

  Returns title, authors, references, funding information, ISSN,
  publisher, publication date, type, and other metadata.

  Args:
    doi: DOI of the work (e.g. '10.1038/nature12373')

  Returns:
    Dict with full work metadata
  """
  url = f"/works/{urllib.parse.quote(doi, safe='')}"
  headers = _env_headers()
  try:
    data = get_client().fetch_json(url)
    if isinstance(data, dict) and "error" in data:
      return data
    return _extract_message(data, field=None)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {"error": f"DOI not found: {doi}", "endpoint": url}
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": url,
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": url,
    }


def get_work_references(doi: str) -> list[dict]:
  """Retrieve the reference list for a scholarly work.

  Returns the references (citation list) that the work cites.

  Args:
    doi: DOI of the work (e.g. '10.1038/nature12373')

  Returns:
    List of reference dicts with DOI, title, year, etc.
  """
  url = f"/works/{urllib.parse.quote(doi, safe='')}/references"
  headers = _env_headers()
  try:
    data = get_client().fetch_json(
        url,
        headers=headers if headers else None,
    )
    if isinstance(data, dict) and "error" in data:
      return data
    return _extract_message(data, "items")
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {"error": f"DOI not found: {doi}", "endpoint": url}
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": url,
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": url,
    }


def search_journals(query: str, limit: int = 20) -> list[dict]:
  """Search CrossRef journals by title or ISSN.

  Args:
    query: Journal title or ISSN search string
    limit: Maximum results to return

  Returns:
    List of journal objects with title, ISSN, publisher, etc.
  """
  params = _env_params() | {
      "query": query,
      "rows": limit,
  }
  headers = _env_headers()
  try:
    data = get_client().fetch_json(
        "/journals",
        params=params if params else None,
    )
    if isinstance(data, dict) and "error" in data:
      return data
    return _extract_message(data, "items")
  except http_client.HttpError as e:
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": "/journals",
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": "/journals",
    }


def get_journal(issn: str) -> dict:
  """Retrieve metadata for a journal by its ISSN.

  Args:
    issn: ISSN of the journal (e.g. '0092-8674')

  Returns:
    Dict with journal metadata including title, ISSNs, publisher, etc.
  """
  url = f"/journals/{issn}"
  headers = _env_headers()
  try:
    data = get_client().fetch_json(url)
    if isinstance(data, dict) and "error" in data:
      return data
    return _extract_message(data, field=None)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {"error": f"ISSN not found: {issn}", "endpoint": url}
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": url,
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": url,
    }


def search_funders(query: str, limit: int = 20) -> list[dict]:
  """Search CrossRef funding organizations.

  Args:
    query: Funder name or identifier search string
    limit: Maximum results to return

  Returns:
    List of funder objects with name, location, DOI, etc.
  """
  params = _env_params() | {
      "query": query,
      "rows": limit,
  }
  headers = _env_headers()
  try:
    data = get_client().fetch_json(
        "/funders",
        params=params if params else None,
    )
    if isinstance(data, dict) and "error" in data:
      return data
    return _extract_message(data, "items")
  except http_client.HttpError as e:
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": "/funders",
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": "/funders",
    }


def get_funder(funder_id: str) -> dict:
  """Retrieve metadata for a specific funding organization.

  Args:
    funder_id: Funder ID (DOI-like, e.g. '10.13039/100000001')

  Returns:
    Dict with funder metadata including name, location, and alternate IDs.
  """
  url = f"/funders/{urllib.parse.quote(funder_id, safe='')}"
  headers = _env_headers()
  try:
    data = get_client().fetch_json(url)
    if isinstance(data, dict) and "error" in data:
      return data
    return _extract_message(data, field=None)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {"error": f"Funder not found: {funder_id}", "endpoint": url}
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": url,
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": url,
    }


def get_agency(doi: str) -> dict:
  """Find which registration agency manages a DOI.

  Args:
    doi: DOI to look up (e.g. '10.1038/nature12373')

  Returns:
    Dict with agency metadata (name, DOI prefix, member ID).
  """
  url = f"/works/{urllib.parse.quote(doi, safe='')}/agency"
  headers = _env_headers()
  try:
    data = get_client().fetch_json(url)
    if isinstance(data, dict) and "error" in data:
      return data
    return _extract_message(data, field=None)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {"error": f"DOI not found: {doi}", "endpoint": url}
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": url,
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": url,
    }


def list_works_by_prefix(prefix: str, limit: int = 20) -> list[dict]:
  """List works registered under a specific DOI prefix.

  Args:
    prefix: DOI prefix (e.g. '10.1038')
    limit: Maximum results to return

  Returns:
    List of work objects registered under the prefix.
  """
  params = _env_params() | {
      "rows": limit,
  }
  headers = _env_headers()
  try:
    data = get_client().fetch_json(
        f"/prefixes/{prefix}/works",
        params=params if params else None,
    )
    if isinstance(data, dict) and "error" in data:
      return data
    return _extract_message(data, "items")
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {"error": f"Prefix not found: {prefix}", "endpoint": f"/prefixes/{prefix}/works"}
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": f"/prefixes/{prefix}/works",
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": f"/prefixes/{prefix}/works",
    }


def get_work_type_distribution(query: str) -> dict:
  """Get the distribution of work types for a query, using CrossRef facets.

  Returns counts per type (journal-article, book-chapter, dataset, etc.)
  so the user can understand the composition of results.

  Args:
    query: Query string to get type distribution for

  Returns:
    Dict mapping work type names to count values.
  """
  params = _env_params() | {
      "query": query,
      "rows": 0,
      "facet": "type:*",
  }
  headers = _env_headers()
  try:
    data = get_client().fetch_json(
        "/works",
        params=params if params else None,
    )
    if isinstance(data, dict) and "error" in data:
      return data
    message = data.get("message", {})
    facets = message.get("facets", {})
    type_facet = facets.get("type", {})
    if isinstance(type_facet, dict) and "values" in type_facet:
      return type_facet["values"]
    return {}
  except http_client.HttpError as e:
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": "/works?facet=type:*",
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": "/works?facet=type:*",
    }


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_works,
        get_work,
        get_work_references,
        search_journals,
        get_journal,
        search_funders,
        get_funder,
        get_agency,
        list_works_by_prefix,
        get_work_type_distribution,
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
    print("Usage: crossref_api.py <output_file> <func> [--flag val]")
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
