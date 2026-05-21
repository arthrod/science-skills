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

r"""Data.gov CKAN API CLI.

Provides command-line access to the Data.gov CKAN catalog API.
Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run scripts/data_gov_api.py search_results.json \
    search_datasets "climate change" --limit 5
  uv run scripts/data_gov_api.py dataset.json \
    get_dataset "db24c0d1-2c29-4c76-9ceb-f5f36504978c"
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

CKAN_BASE = "https://catalog.data.gov/api/3"

_CKAN_CLIENT = None


def get_ckan_client():
  """Returns the lazily initialized CKAN HttpClient."""
  global _CKAN_CLIENT
  if _CKAN_CLIENT is None:
    _CKAN_CLIENT = http_client.HttpClient(CKAN_BASE, qps=5)
  return _CKAN_CLIENT


_ACTION_URL = "/action"


def _get(action_path, params=None):
  """GET request to the CKAN action API with retry logic."""
  url = f"{_ACTION_URL}/{action_path}"
  if params:
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    if qs:
      url = f"{url}?{qs}"
  try:
    return get_ckan_client().fetch_json(url)
  except http_client.HttpError as e:
    if e.status_code == 404:
      return {"error": "Record not found (HTTP 404).", "endpoint": url}
    else:
      return {"error": f"HTTP Error {e.status_code or 'Error'}: {str(e)}", "endpoint": url}
  except json.JSONDecodeError as e:
    body_snippet = str(e.doc)[:500] if hasattr(e, "doc") else str(e)
    return {"error": f"Failed to parse JSON response. Body: {body_snippet}", "endpoint": url}


def search_datasets(
    query: str,
    topic: str = "",
    format: str = "",
    limit: int = 20,
) -> list[dict]:
  """Search US government datasets by keyword, topic, and file format.

  Uses the CKAN package_search action. Returns a list of dataset dicts with
  metadata including title, description, organization, and resources.

  Args:
    query: Free-text search query for datasets
    topic: Optional filter by topic/category
    format: Optional filter by file format (e.g. CSV, JSON, PDF)
    limit: Maximum number of results to return (default 20)

  Returns:
    List of dataset dicts with metadata and resources
  """
  q_parts = [query]
  if topic:
    q_parts.append(f"topic:{topic}")
  params = {
      "q": " ".join(q_parts),
      "rows": limit,
  }
  data = _get("package_search", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    results = data.get("result", {}).get("results", [])
    if format:
      filtered = []
      for ds in results:
        resources = ds.get("resources", [])
        if any(r.get("format", "").lower() == format.lower() for r in resources):
          filtered.append(ds)
      results = filtered
    return results
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected package_search response structure", "endpoint": "package_search"}


def get_dataset(dataset_id: str) -> dict:
  """Retrieve full metadata for a specific dataset by its ID.

  Uses the CKAN package_show action. Returns dataset metadata including all
  resources (downloadable files), organization, tags, and groups.

  Args:
    dataset_id: The dataset UUID or name

  Returns:
    Dict with full dataset metadata including resources
  """
  params = {"id": dataset_id}
  data = _get("package_show", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    return data.get("result", {})
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected package_show response structure", "endpoint": "package_show"}


def get_dataset_show(package_id: str) -> dict:
  """Retrieve package details by ID or name.

  Alias for get_dataset; uses the CKAN package_show action.

  Args:
    package_id: The package ID or name

  Returns:
    Dict with full package metadata
  """
  params = {"id": package_id}
  data = _get("package_show", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    return data.get("result", {})
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected package_show response structure", "endpoint": "package_show"}


def get_organization(org_name: str) -> dict:
  """Get details about a specific organization (agency/department).

  Uses the CKAN organization_show action. Returns metadata about the
  organization including title, description, and its datasets.

  Args:
    org_name: Organization name or ID

  Returns:
    Dict with organization metadata and datasets
  """
  params = {"id": org_name, "include_datasets": True}
  data = _get("organization_show", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    return data.get("result", {})
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected organization_show response structure", "endpoint": "organization_show"}


def list_organizations(limit: int = 50) -> list[dict]:
  """List all organizations (agencies/departments) on Data.gov.

  Uses the CKAN organization_list action. Returns a list of all organizations
  with basic metadata.

  Args:
    limit: Maximum number of organizations to return (default 50)

  Returns:
    List of organization dicts
  """
  params = {"all_fields": True, "limit": limit}
  data = _get("organization_list", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    return data.get("result", [])
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected organization_list response structure", "endpoint": "organization_list"}


def get_group(group_name: str) -> dict:
  """Get details about a specific group (topic/category).

  Uses the CKAN group_show action. Returns metadata about the group
  including title, description, and its datasets.

  Args:
    group_name: Group name or ID

  Returns:
    Dict with group metadata and datasets
  """
  params = {"id": group_name, "include_datasets": True}
  data = _get("group_show", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    return data.get("result", {})
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected group_show response structure", "endpoint": "group_show"}


def list_groups(limit: int = 50) -> list[dict]:
  """List all groups (topics/categories) on Data.gov.

  Uses the CKAN group_list action. Returns a list of all groups
  with basic metadata.

  Args:
    limit: Maximum number of groups to return (default 50)

  Returns:
    List of group dicts
  """
  params = {"all_fields": True, "limit": limit}
  data = _get("group_list", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    return data.get("result", [])
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected group_list response structure", "endpoint": "group_list"}


def get_resource(resource_id: str) -> dict:
  """Get details about a specific resource file.

  Uses the CKAN resource_show action. Returns metadata about the resource
  including download URL, format, size, and description.

  Args:
    resource_id: Resource UUID

  Returns:
    Dict with resource metadata including download URL
  """
  params = {"id": resource_id}
  data = _get("resource_show", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    return data.get("result", {})
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected resource_show response structure", "endpoint": "resource_show"}


def search_tags(query: str, limit: int = 20) -> list[dict]:
  """Search datasets by keyword tag.

  Uses the CKAN tag_show action. Returns tag metadata and datasets
  associated with matching tags.

  Args:
    query: Tag keyword to search for
    limit: Maximum number of results to return (default 20)

  Returns:
    List of tag dicts with associated datasets
  """
  params = {"query": query, "limit": limit}
  data = _get("tag_show", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    result = data.get("result", {})
    return result.get("packages", []) if isinstance(result, dict) else result
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected tag_show response structure", "endpoint": "tag_show"}


def list_tags(limit: int = 50) -> list[str]:
  """List all tags used on Data.gov.

  Uses the CKAN tag_list action. Returns a list of all tag names.

  Args:
    limit: Maximum number of tags to return (default 50)

  Returns:
    List of tag name strings
  """
  params = {"all_fields": False, "limit": limit}
  data = _get("tag_list", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    return data.get("result", [])
  except (KeyError, TypeError, AttributeError):
    return {"error": "Unexpected tag_list response structure", "endpoint": "tag_list"}


def get_recent_datasets(limit: int = 20) -> list[dict]:
  """Get recently added or updated datasets.

  Uses the CKAN current_package_list_with_resources action. Returns the most
  recently created/updated datasets with their resources included.

  Args:
    limit: Maximum number of datasets to return (default 20)

  Returns:
    List of recent dataset dicts with resources
  """
  params = {"limit": limit}
  data = _get("current_package_list_with_resources", params)
  if isinstance(data, dict) and "error" in data:
    return data
  try:
    return data.get("result", [])
  except (KeyError, TypeError, AttributeError):
    return {
        "error": "Unexpected current_package_list_with_resources response structure",
        "endpoint": "current_package_list_with_resources",
    }


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_datasets,
        get_dataset,
        get_dataset_show,
        get_organization,
        list_organizations,
        get_group,
        list_groups,
        get_resource,
        search_tags,
        list_tags,
        get_recent_datasets,
    ]
}


def _is_list_type(annotation):
  origin = getattr(annotation, "__origin__", None)
  return origin is list


def _coerce_arg(value: str, annotation):
  if _is_list_type(annotation):
    return [v.strip() for v in value.split(",")]
  if annotation is int:
    return int(value)
  return value


def main():
  if len(sys.argv) < 3:
    print("Usage: data_gov_api.py <output_file> <func> [--flag val]")
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
