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

r"""Semantic Scholar API CLI.

Provides command-line access to the Semantic Scholar Graph API and
Recommendations API. Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run semantic_scholar_api.py search_results.json \
    search_papers "transformer attention" --limit 5
  uv run semantic_scholar_api.py paper_details.json \
    get_paper_details "CorpusId:215416146"
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

S2_API_BASE = "https://api.semanticscholar.org/graph/v1/"
S2_RECOMMENDATIONS_BASE = "https://api.semanticscholar.org/recommendations/v1/"

_S2_CLIENT = None


def get_s2_client():
  """Returns the lazily initialized Semantic Scholar HttpClient."""
  global _S2_CLIENT
  if _S2_CLIENT is None:
    qps = 100 if os.environ.get("S2_API_KEY") else 1
    _S2_CLIENT = http_client.HttpClient(S2_API_BASE, qps=qps)
  return _S2_CLIENT


_MAX_JSON_ERROR_SNIPPET_LENGTH = 500


def _get_headers():
  """Returns auth headers if S2_API_KEY is set."""
  headers = {}
  api_key = os.environ.get("S2_API_KEY")
  if api_key:
    headers["x-api-key"] = api_key
  return headers


def _get(url, params=None, *, client=None):
  """GET request with retry logic and rate limiting."""
  if client is None:
    client = get_s2_client()

  if params:
    query_string = urllib.parse.urlencode(params, doseq=True)
    url = url + "?" + query_string

  try:
    return client.fetch_json(url, headers=_get_headers())
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


def _post(url, json_body, *, client=None):
  """POST request with JSON body."""
  if client is None:
    client = get_s2_client()
  try:
    return client.fetch_json(
        url,
        method="POST",
        json_body=json_body,
        headers=_get_headers(),
    )
  except http_client.HttpError as e:
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": url,
    }
  except json.JSONDecodeError as e:
    body_snippet = e.doc
    if len(body_snippet) > _MAX_JSON_ERROR_SNIPPET_LENGTH:
      body_snippet = f"{body_snippet[:_MAX_JSON_ERROR_SNIPPET_LENGTH]}..."
    return {
        "error": f"Failed to parse JSON response. Body: {body_snippet}",
        "endpoint": url,
    }


def search_papers(
    query: str,
    limit: int = 10,
    fields: str = "title,authors,year,venue,citationCount,openAccessPdf",
) -> list[dict]:
  """Searches papers by query string.

  Args:
    query: Free-text search query
    limit: Maximum number of results to return (max 100)
    fields: Comma-separated field list for the response

  Returns:
    List of paper dicts with the requested fields
  """
  params = {
      "query": query,
      "limit": limit,
      "fields": fields,
  }
  data = _get(f"{S2_API_BASE}paper/search", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data.get("data", [])


def search_by_ids(
    ids_json: str,
    id_type: str = "DOI",
    fields: str = "title,authors,year,venue,citationCount,openAccessPdf",
) -> list[dict]:
  """Looks up papers by external IDs.

  Args:
    ids_json: JSON array of IDs (e.g. '["10.1234/abc","10.5678/def"]')
    id_type: Type of IDs — DOI, ArXiv, PubMed, ACL, CorpusId, PaperId
    fields: Comma-separated field list for the response

  Returns:
    List of paper dicts with the requested fields
  """
  ids = json.loads(ids_json)
  body = {"ids": [f"{id_type}:{i}" for i in ids]}
  data = _post(f"{S2_API_BASE}paper/batch?fields={fields}", body)
  if isinstance(data, dict) and "error" in data:
    return data
  # Filter out None entries (IDs not found)
  return [p for p in data if p is not None] if isinstance(data, list) else data


def get_recommendations(
    paper_id: str,
    limit: int = 10,
) -> list[dict]:
  """Gets paper recommendations based on a seed paper.

  Args:
    paper_id: S2 PaperId (e.g. "CorpusId:215416146" or "649def34f8f...")
    limit: Maximum number of recommendations

  Returns:
    List of recommended paper dicts
  """
  params = {"limit": limit}
  data = _get(
      f"{S2_RECOMMENDATIONS_BASE}recommendations/{paper_id}",
      params,
  )
  if isinstance(data, dict) and "error" in data:
    return data
  return data.get("recommendedPapers", [])


def get_paper_details(
    paper_id: str,
    fields: str = "title,abstract,authors,year,venue,citationCount,referenceCount,tldr,embedding",
) -> dict:
  """Gets full details for a single paper.

  Args:
    paper_id: S2 PaperId (e.g. "CorpusId:215416146" or "649def34f8f...")
    fields: Comma-separated field list for the response

  Returns:
    Dict with paper details including abstract, authors, citations, references
  """
  params = {"fields": fields}
  data = _get(f"{S2_API_BASE}paper/{paper_id}", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def get_bulk_papers(
    ids_json: str,
    fields: str = "title,authors,year,venue,citationCount,abstract",
) -> list[dict]:
  """Fetches multiple papers in one POST request.

  Args:
    ids_json: JSON array of S2 PaperIds
      (e.g. '["CorpusId:215416146","CorpusId:12345678"]')
    fields: Comma-separated field list for the response

  Returns:
    List of paper dicts
  """
  ids = json.loads(ids_json)
  params = {"fields": fields}
  body = {"ids": ids}
  data = _post(f"{S2_API_BASE}paper/batch", body)
  if isinstance(data, dict) and "error" in data:
    return data
  return [p for p in data if p is not None] if isinstance(data, list) else data


def get_author_details(
    author_id: str,
    fields: str = "name,hIndex,papers,paperCount,citationCount",
) -> dict:
  """Gets author profile with papers, stats, and h-index.

  Args:
    author_id: S2 AuthorId (e.g. "1741101")
    fields: Comma-separated field list for the response

  Returns:
    Dict with author details
  """
  params = {"fields": fields}
  data = _get(f"{S2_API_BASE}author/{author_id}", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def get_paper_citations(
    paper_id: str,
    limit: int = 100,
    fields: str = "title,authors,year,venue,citationCount",
) -> list[dict]:
  """Gets papers citing a given paper.

  Args:
    paper_id: S2 PaperId
    limit: Maximum number of citations to return
    fields: Comma-separated field list for the response

  Returns:
    List of citing paper entries, each with a 'citingPaper' key
  """
  params = {"limit": limit, "fields": fields}
  data = _get(f"{S2_API_BASE}paper/{paper_id}/citations", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data.get("data", [])


def get_paper_references(
    paper_id: str,
    limit: int = 100,
    fields: str = "title,authors,year,venue,citationCount",
) -> list[dict]:
  """Gets papers referenced by a given paper.

  Args:
    paper_id: S2 PaperId
    limit: Maximum number of references to return
    fields: Comma-separated field list for the response

  Returns:
    List of referenced paper entries, each with a 'citedPaper' key
  """
  params = {"limit": limit, "fields": fields}
  data = _get(f"{S2_API_BASE}paper/{paper_id}/references", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data.get("data", [])


def get_paper_embeddings(
    ids_json: str,
    model: str = "specter2",
) -> list[dict]:
  """Gets SPECTER/SPECTER2 embeddings for papers.

  Args:
    ids_json: JSON array of S2 PaperIds
    model: Embedding model — "specter" or "specter2"

  Returns:
    List of dicts with paperId and embedding
  """
  ids = json.loads(ids_json)
  body = {"ids": ids}
  data = _post(f"{S2_API_BASE}paper/embeddings?model={model}", body)
  if isinstance(data, dict) and "error" in data:
    return data
  return data if isinstance(data, list) else data.get("data", [])


def get_tldr(
    ids_json: str,
) -> list[dict]:
  """Gets TLDR (too long; didn't read) summaries for papers.

  Args:
    ids_json: JSON array of S2 PaperIds

  Returns:
    List of dicts with paperId and tldr (model, text)
  """
  ids = json.loads(ids_json)
  params = {"fields": "tldr"}
  data = _post(f"{S2_API_BASE}paper/batch", {"ids": ids})
  if isinstance(data, dict) and "error" in data:
    return data
  results = [p for p in data if p is not None] if isinstance(data, list) else data
  # Extract paperId + tldr from each result
  return [{"paperId": r.get("paperId"), "tldr": r.get("tldr")} for r in results]


def search_papers_batch(
    query: str,
    offset: int = 0,
    limit: int = 100,
) -> list[dict]:
  """Cursor-based pagination for large search result sets.

  Args:
    query: Free-text search query
    offset: Number of results to skip (for pagination)
    limit: Maximum number of results to return (max 100 per page)

  Returns:
    List of paper dicts
  """
  params = {
      "query": query,
      "offset": offset,
      "limit": limit,
      "fields": "title,authors,year,venue,citationCount",
  }
  data = _get(f"{S2_API_BASE}paper/search", params)
  if isinstance(data, dict) and "error" in data:
    return data
  return data.get("data", [])


def batch_export_metadata(
    ids_json: str,
    fields: str = "title,authors,year,venue,citationCount,abstract,publicationDate",
) -> list[dict]:
  """Bulk exports metadata from a list of IDs.

  Args:
    ids_json: JSON array of S2 PaperIds
    fields: Comma-separated field list for the response

  Returns:
    List of paper dicts
  """
  ids = json.loads(ids_json)
  params = {"fields": fields}
  body = {"ids": ids}
  data = _post(f"{S2_API_BASE}paper/batch", body)
  if isinstance(data, dict) and "error" in data:
    return data
  return [p for p in data if p is not None] if isinstance(data, list) else data


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_papers,
        search_by_ids,
        get_recommendations,
        get_paper_details,
        get_bulk_papers,
        get_author_details,
        get_paper_citations,
        get_paper_references,
        get_paper_embeddings,
        get_tldr,
        search_papers_batch,
        batch_export_metadata,
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
    print("Usage: semantic_scholar_api.py <output_file> <func> [--flag val]")
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
