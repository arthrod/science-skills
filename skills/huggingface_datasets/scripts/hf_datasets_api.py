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

r"""Hugging Face Datasets API CLI.

Provides command-line access to the Hugging Face Datasets Server API.
Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run hf_datasets_api.py search_results.json \
    search_datasets "question answering" --task text-classification --limit 5
  uv run hf_datasets_api.py dataset_info.json \
    get_dataset "squad"
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

HF_API_BASE = "https://huggingface.co/api/datasets"

_CLIENT = None


def get_client():
  """Returns the lazily initialized HttpClient for HF Datasets API."""
  global _CLIENT
  if _CLIENT is None:
    headers = {}
    api_key = os.environ.get("HF_API_KEY")
    if api_key:
      headers["Authorization"] = f"Bearer {api_key}"
    _CLIENT = http_client.HttpClient(
        "https://huggingface.co/",
        qps=10,
        default_headers=headers,
    )
  return _CLIENT


def _get(path, params=None):
  """GET request with retry logic and rate limiting."""
  client = get_client()
  url = path.lstrip("/")
  if params:
    url = url + "?" + urllib.parse.urlencode(params)
  try:
    return client.fetch_json(url)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {"error": "Not found (HTTP 404).", "endpoint": url}
    return {
        "error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}",
        "endpoint": url,
    }
  except json.JSONDecodeError as e:
    return {
        "error": f"Failed to parse JSON response: {e}",
        "endpoint": url,
    }


def search_datasets(
    query: str,
    task: str = "",
    language: str = "",
    limit: int = 20,
) -> list[dict]:
  """Searches datasets on Hugging Face by query string.

  Uses the /api/datasets endpoint with search parameter. Optionally filters
  by task category and/or language code.

  Args:
    query: Search query string (matched against dataset names, descriptions)
    task: Optional task category filter (e.g. 'text-classification',
      'question-answering', 'summarization', 'translation')
    language: Optional language code filter (e.g. 'en', 'fr', 'de', 'multilingual')
    limit: Maximum number of results to return (default: 20)

  Returns:
    List of dataset metadata dicts, each with id, description, tags, etc.
  """
  params: dict[str, str | int] = {"search": query}
  if task:
    params["task_categories"] = task
  if language:
    params["languages"] = language
  params["full"] = "false"
  if limit:
    params["limit"] = limit

  data = _get("/api/datasets", params)
  if isinstance(data, dict) and "error" in data:
    return data
  if not isinstance(data, list):
    return {"error": "Unexpected response format", "endpoint": "/api/datasets"}
  return data[:limit]


def get_dataset(dataset_name: str) -> dict:
  """Gets detailed metadata for a specific dataset.

  Retrieves the full dataset card information including configs, tags,
  download counts, file listings, and card README content.

  Args:
    dataset_name: Dataset identifier (e.g. 'squad', 'imdb',
      'bigscience-data/P3')

  Returns:
    Dict with full dataset metadata
  """
  path = f"/api/datasets/{urllib.parse.quote(dataset_name, safe='')}"
  data = _get(path)
  if isinstance(data, dict) and "error" in data:
    return data
  return data


def list_datasets_by_task(task: str, limit: int = 20) -> list[dict]:
  """Lists datasets filtered by NLP task category.

  Args:
    task: Task category (e.g. 'text-classification', 'question-answering',
      'summarization', 'translation', 'text-generation', 'token-classification')
    limit: Maximum number of results (default: 20)

  Returns:
    List of dataset metadata dicts matching the task
  """
  params: dict[str, str | int] = {
      "full": "false",
      "task_categories": task,
  }
  if limit:
    params["limit"] = limit

  data = _get("/api/datasets", params)
  if isinstance(data, dict) and "error" in data:
    return data
  if not isinstance(data, list):
    return {"error": "Unexpected response format", "endpoint": "/api/datasets"}
  return data[:limit]


def list_dataset_configs(dataset_name: str) -> list[dict]:
  """Lists available configurations/splits for a dataset.

  Each dataset can have multiple configurations (e.g. different subsets,
  languages, versions). This endpoint returns the available configs and
  their split details.

  Args:
    dataset_name: Dataset identifier (e.g. 'squad', 'imdb')

  Returns:
    List of config dicts each with config name, data files, and split info
  """
  path = f"/api/datasets/{urllib.parse.quote(dataset_name, safe='')}"
  data = _get(path)
  if isinstance(data, dict) and "error" in data:
    return data
  configs = data.get("configs", []) if isinstance(data, dict) else []
  return configs


def get_dataset_parquet_urls(
    dataset_name: str,
    config: str = "",
    split: str = "",
) -> list[str]:
  """Gets Parquet download URLs for a dataset.

  Hugging Face automatically converts datasets to Parquet format. This
  returns the direct download URLs for use with tools like DuckDB, Polars,
  or Pandas.

  Args:
    dataset_name: Dataset identifier (e.g. 'squad', 'imdb')
    config: Optional config name to filter by
    split: Optional split name to filter by (e.g. 'train', 'test', 'validation')

  Returns:
    List of Parquet file download URLs
  """
  path = f"/api/datasets/{urllib.parse.quote(dataset_name, safe='')}/parquet"
  params: dict[str, str] = {}
  if config:
    params["config"] = config
  if split:
    params["split"] = split

  data = _get(path, params)
  if isinstance(data, dict) and "error" in data:
    return data
  if not isinstance(data, list):
    return {"error": "Unexpected parquet response format", "endpoint": path}

  urls = []
  for entry in data:
    if isinstance(entry, dict):
      urls.extend(entry.get("urls", []))
  return urls


def get_dataset_card(dataset_name: str) -> str:
  """Gets the dataset README/card markdown content.

  Retrieves the human-readable dataset card (README) content in markdown
  format. This contains descriptions, intended uses, limitations, and
  licensing information.

  Args:
    dataset_name: Dataset identifier (e.g. 'squad', 'imdb')

  Returns:
    String containing the dataset card markdown content
  """
  path = f"/api/datasets/{urllib.parse.quote(dataset_name, safe='')}"
  data = _get(path)
  if isinstance(data, dict) and "error" in data:
    return data
  if isinstance(data, dict):
    card_data = data.get("cardData", {}) or {}
    if not card_data:
      return {"dataset": dataset_name, "card": ""}
    return {"dataset": dataset_name, "card": json.dumps(card_data, indent=2)}
  return {"error": "Unexpected response format", "endpoint": path}


def get_dataset_tags(dataset_name: str) -> dict[str, list[str]]:
  """Gets all tags associated with a dataset.

  Returns tags grouped by category: languages, tasks (annotations),
  licenses, sizes, and other tags.

  Args:
    dataset_name: Dataset identifier (e.g. 'squad', 'imdb')

  Returns:
    Dict with keys like 'languages', 'tasks', 'licenses', 'sizes', 'other'
    each mapping to a list of tag strings
  """
  path = f"/api/datasets/{urllib.parse.quote(dataset_name, safe='')}"
  data = _get(path)
  if isinstance(data, dict) and "error" in data:
    return data
  if not isinstance(data, dict):
    return {"error": "Unexpected response format", "endpoint": path}

  tags = data.get("tags", [])
  if not isinstance(tags, list):
    return {"dataset": dataset_name, "languages": [], "tasks": [],
            "licenses": [], "sizes": [], "other": []}

  languages = []
  tasks = []
  licenses_tags = []
  sizes = []
  other = []
  for tag in tags:
    if tag.startswith("languages:"):
      languages.append(tag.replace("languages:", ""))
    elif tag.startswith("annotations:"):
      tasks.append(tag.replace("annotations:", ""))
    elif tag.startswith("licenses:"):
      licenses_tags.append(tag.replace("licenses:", ""))
    elif tag.startswith("sizes:"):
      sizes.append(tag.replace("sizes:", ""))
    else:
      other.append(tag)

  return {
      "dataset": dataset_name,
      "languages": languages,
      "tasks": tasks,
      "licenses": licenses_tags,
      "sizes": sizes,
      "other": other,
  }


def list_datasets_by_language(
    language: str,
    limit: int = 20,
) -> list[dict]:
  """Lists datasets filtered by language code.

  Args:
    language: Language code (e.g. 'en', 'fr', 'de', 'es', 'zh', 'multilingual')
    limit: Maximum number of results (default: 20)

  Returns:
    List of dataset metadata dicts matching the language
  """
  params: dict[str, str | int] = {
      "full": "false",
      "languages": language,
  }
  if limit:
    params["limit"] = limit

  data = _get("/api/datasets", params)
  if isinstance(data, dict) and "error" in data:
    return data
  if not isinstance(data, list):
    return {"error": "Unexpected response format", "endpoint": "/api/datasets"}
  return data[:limit]


def get_dataset_downloads(dataset_name: str) -> dict:
  """Gets download count and trending statistics for a dataset.

  Args:
    dataset_name: Dataset identifier (e.g. 'squad', 'imdb')

  Returns:
    Dict with download statistics including total downloads and
    recent downloads
  """
  path = f"/api/datasets/{urllib.parse.quote(dataset_name, safe='')}"
  data = _get(path)
  if isinstance(data, dict) and "error" in data:
    return data
  if not isinstance(data, dict):
    return {"error": "Unexpected response format", "endpoint": path}

  return {
      "dataset": dataset_name,
      "downloads": data.get("downloads", 0),
      "likes": data.get("likes", 0),
  }


def list_trending_datasets(limit: int = 20) -> list[dict]:
  """Lists the most downloaded datasets on Hugging Face recently.

  Uses the datasets list endpoint sorted by download count.

  Args:
    limit: Maximum number of results (default: 20)

  Returns:
    List of dataset metadata dicts sorted by download count
  """
  params: dict[str, str | int] = {
      "full": "false",
      "sort": "downloads",
      "direction": -1,
  }
  if limit:
    params["limit"] = limit

  data = _get("/api/datasets", params)
  if isinstance(data, dict) and "error" in data:
    return data
  if not isinstance(data, list):
    return {"error": "Unexpected response format", "endpoint": "/api/datasets"}
  return data[:limit]


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_datasets,
        get_dataset,
        list_datasets_by_task,
        list_dataset_configs,
        get_dataset_parquet_urls,
        get_dataset_card,
        get_dataset_tags,
        list_datasets_by_language,
        get_dataset_downloads,
        list_trending_datasets,
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
    print("Usage: hf_datasets_api.py <output_file> <func> [--flag val]")
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
