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

r"""Papers With Code API CLI.

Provides command-line access to the Papers With Code API.
Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run pwc_api.py search_results.json \
    search_papers "transformer attention" 10
  uv run pwc_api.py paper.json \
    get_paper "attention-is-all-you-need"
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

PWC_BASE = "https://paperswithcode.com/api/v1"

_PWC_CLIENT = None


def get_pwc_client():
  """Returns the lazily initialized PWC HttpClient."""
  global _PWC_CLIENT
  if _PWC_CLIENT is None:
    headers = {}
    api_key = os.environ.get("PWC_API_KEY")
    if api_key:
      headers["Authorization"] = f"Token {api_key}"
    _PWC_CLIENT = http_client.HttpClient(
        PWC_BASE, qps=5, default_headers=headers
    )
  return _PWC_CLIENT


_MAX_JSON_ERROR_SNIPPET_LENGTH = 500


def _get(path, params=None):
  """GET request with retry logic and rate limiting."""
  if params:
    qs = urllib.parse.urlencode(params)
    url = f"{path}?{qs}"
  else:
    url = path

  try:
    return get_pwc_client().fetch_json(url)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {
          "error": "Record not found (HTTP 404).",
          "endpoint": path,
      }
    else:
      return {
          "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
          "endpoint": path,
      }
  except json.JSONDecodeError as e:
    body_snippet = e.doc
    if len(body_snippet) > _MAX_JSON_ERROR_SNIPPET_LENGTH:
      body_snippet = f"{body_snippet[:_MAX_JSON_ERROR_SNIPPET_LENGTH]}..."
    return {
        "error": f"Failed to parse JSON response. Body: {body_snippet}",
        "endpoint": path,
    }


# ---------------------------------------------------------------------------
# Paper search & retrieval
# ---------------------------------------------------------------------------


def search_papers(query: str, limit: int = 50) -> dict:
  """Searches papers by query string.

  Args:
    query: Free-text search query.
    limit: Maximum number of results to return (default 50, max ~500).

  Returns:
    Dict with 'count', 'next', 'previous', and 'results' list.
    Each result contains id, title, abstract, url_abs, url_pdf, etc.
  """
  path = "/papers/"
  params = {"q": query, "items_per_page": min(limit, 500)}
  return _get(path, params)


def get_paper(paper_id: str) -> dict:
  """Gets paper details by its PWC paper ID (slug).

  Args:
    paper_id: Paper ID string (e.g. 'attention-is-all-you-need').

  Returns:
    Dict with paper fields: id, title, abstract, url_abs, url_pdf,
    pwc_url, publishing_info, etc.
  """
  paper_id_enc = urllib.parse.quote(paper_id, safe="")
  path = f"/papers/{paper_id_enc}/"
  return _get(path)


def get_paper_results(paper_id: str) -> dict:
  """Gets evaluation results / leaderboard entries for a paper.

  Args:
    paper_id: Paper ID string (e.g. 'attention-is-all-you-need').

  Returns:
    Dict with 'count' and 'results' list. Each result contains
    task, model, metrics, dataset, etc.
  """
  paper_id_enc = urllib.parse.quote(paper_id, safe="")
  path = f"/papers/{paper_id_enc}/results/"
  return _get(path)


# ---------------------------------------------------------------------------
# Tasks & Benchmarks
# ---------------------------------------------------------------------------


def search_tasks(query: str, limit: int = 50) -> dict:
  """Searches ML tasks by query string.

  Args:
    query: Free-text search query for tasks.
    limit: Maximum number of results to return.

  Returns:
    Dict with 'count', 'next', 'previous', and 'results' list.
    Each result contains id, name, description, etc.
  """
  path = "/tasks/"
  params = {"q": query, "items_per_page": min(limit, 500)}
  return _get(path, params)


def get_task(task_id: str) -> dict:
  """Gets task details by its PWC task ID (slug).

  Args:
    task_id: Task ID string (e.g. 'image-classification').

  Returns:
    Dict with task fields: id, name, description, image, etc.
  """
  task_id_enc = urllib.parse.quote(task_id, safe="")
  path = f"/tasks/{task_id_enc}/"
  return _get(path)


def get_task_leaderboard(task_id: str) -> dict:
  """Gets the SOTA leaderboard for a task.

  Args:
    task_id: Task ID string (e.g. 'image-classification').

  Returns:
    Dict with 'count' and 'results' list. Each result contains
    model, paper, metrics, dataset, etc. in rank order.
  """
  task_id_enc = urllib.parse.quote(task_id, safe="")
  path = f"/tasks/{task_id_enc}/leaderboard/"
  return _get(path)


# ---------------------------------------------------------------------------
# Datasets & Code
# ---------------------------------------------------------------------------


def get_paper_code(paper_id: str) -> dict:
  """Gets code repository links for a paper.

  Args:
    paper_id: Paper ID string (e.g. 'attention-is-all-you-need').

  Returns:
    Dict with 'count' and 'results' list. Each result contains
    url, owner, name, description, framework, stars, etc.
  """
  paper_id_enc = urllib.parse.quote(paper_id, safe="")
  path = f"/papers/{paper_id_enc}/repositories/"
  return _get(path)


def get_datasets(paper_id: str) -> dict:
  """Gets datasets used by a paper.

  Args:
    paper_id: Paper ID string (e.g. 'attention-is-all-you-need').

  Returns:
    Dict with 'count' and 'results' list. Each result contains
    dataset id, name, url, etc.
  """
  paper_id_enc = urllib.parse.quote(paper_id, safe="")
  path = f"/papers/{paper_id_enc}/datasets/"
  return _get(path)


def search_datasets(query: str, limit: int = 50) -> dict:
  """Searches datasets by query string.

  Args:
    query: Free-text search query for datasets.
    limit: Maximum number of results to return.

  Returns:
    Dict with 'count', 'next', 'previous', and 'results' list.
    Each result contains id, name, url, description, etc.
  """
  path = "/datasets/"
  params = {"q": query, "items_per_page": min(limit, 500)}
  return _get(path, params)


def get_dataset(dataset_id: str) -> dict:
  """Gets dataset details and papers using it.

  Args:
    dataset_id: Dataset ID string (e.g. 'cifar-10').

  Returns:
    Dict with dataset fields: id, name, url, description, papers, etc.
  """
  dataset_id_enc = urllib.parse.quote(dataset_id, safe="")
  path = f"/datasets/{dataset_id_enc}/"
  return _get(path)


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_papers,
        get_paper,
        get_paper_results,
        search_tasks,
        get_task,
        get_task_leaderboard,
        get_paper_code,
        get_datasets,
        search_datasets,
        get_dataset,
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
    print("Usage: pwc_api.py <output_file> <func> [--flag val]")
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
    count = result.get("count", len(result.keys()))
    print(f"API call OK: {count} results written to {output_file}")
  else:
    print(f"API call OK: result written to {output_file}")


if __name__ == "__main__":
  main()
