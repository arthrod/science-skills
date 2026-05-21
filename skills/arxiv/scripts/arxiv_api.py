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

r"""arXiv API CLI.

Provides command-line access to the arXiv query API (export.arxiv.org).
Outputs JSON to stdout; all diagnostics go to stderr.

Usage:
  uv run arxiv_api.py search_results.json \
    search_papers "transformer attention" 20
  uv run arxiv_api.py paper_2305.10601.json \
    get_paper "2305.10601"
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
import xml.etree.ElementTree as ET

import dotenv
from science_skills.science_skills_common import http_client

ARXIV_API_BASE = "http://export.arxiv.org/api/query"
# arXiv terms: max 1 request per 3 seconds
ARXIV_QPS = 1.0 / 3.0

_ARXIV_CLIENT = None


def get_arxiv_client():
  """Returns the lazily initialized arXiv HttpClient."""
  global _ARXIV_CLIENT
  if _ARXIV_CLIENT is None:
    _ARXIV_CLIENT = http_client.HttpClient(
        ARXIV_API_BASE, qps=ARXIV_QPS
    )
  return _ARXIV_CLIENT


_ATOM_NS = "{http://www.w3.org/2005/Atom}"
_ARXIV_NS = "{http://arxiv.org/schemas/atom}"
_OPENSEARCH_NS = "{http://a9.com/-/spec/opensearch/1.1/}"


def strip_ns(tag: str) -> str:
  """Strip the namespace prefix from an XML element tag."""
  if tag.startswith("{"):
    return tag.split("}", 1)[1]
  return tag


def _env_params():
  """Returns a dictionary of parameters from the environment."""
  params = {}
  email = os.environ.get("USER_EMAIL")
  if email:
    params["user_email"] = email
  return params


def _build_query_url(params: dict) -> str:
  """Build a full arXiv API query URL from parameters.

  Uses quote_plus so spaces become '+' as required by the arXiv API.
  """
  query_string = urllib.parse.urlencode(
      params, quote_via=urllib.parse.quote_plus
  )
  return f"{ARXIV_API_BASE}?{query_string}"


def _parse_entry(entry: ET.Element) -> dict:
  """Parse a single Atom <entry> element into a paper dict."""
  paper = {}
  authors = []

  for child in entry:
    tag = strip_ns(child.tag)

    if tag == "id":
      # e.g. http://arxiv.org/abs/2305.10601v1 -> 2305.10601v1
      if child.text:
        paper["id"] = child.text.split("/abs/")[-1]
    elif tag == "title":
      paper["title"] = (
          child.text.replace("\n", " ").strip() if child.text else ""
      )
    elif tag == "summary":
      paper["summary"] = (
          child.text.replace("\n", " ").strip() if child.text else ""
      )
    elif tag == "published":
      paper["published"] = child.text
    elif tag == "updated":
      paper["updated"] = child.text
    elif tag == "author":
      name_elem = child.find(f"{_ATOM_NS}name")
      if name_elem is not None and name_elem.text:
        authors.append(name_elem.text)
    elif tag == "link":
      if child.get("title") == "pdf":
        paper["pdf_url"] = child.get("href")
      elif child.get("rel") == "alternate" and "pdf" not in (
          child.get("title") or ""
      ):
        paper["arxiv_url"] = child.get("href")
    elif tag == "primary_category":
      paper["primary_category"] = child.get("term")
    elif tag == "category":
      paper.setdefault("categories", []).append(child.get("term"))
    elif tag == "doi":
      paper["doi"] = child.text
    elif tag == "journal_ref":
      paper["journal_ref"] = child.text
    elif tag == "comment":
      paper["comment"] = child.text

  paper["authors"] = authors
  return paper


def _fetch_and_parse(url: str) -> list[dict]:
  """Fetch XML from arXiv API and parse entries into a list of paper dicts."""
  client = get_arxiv_client()
  xml_data = client.fetch_bytes(url)
  root = ET.fromstring(xml_data)

  papers = []
  for entry in root.findall(f"{_ATOM_NS}entry"):
    papers.append(_parse_entry(entry))

  return papers


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------


def search_papers(
    query: str,
    limit: int = 20,
    sort_by: str = "relevance",
) -> list[dict]:
  """Search arXiv by free-text query.

  Supports arXiv query syntax including field prefixes (ti:, au:, abs:,
  cat:), Boolean operators (AND, OR, ANDNOT), grouping with parentheses,
  and exact phrase matching with double quotes.

  The sort_by parameter accepts 'relevance', 'submittedDate', or
  'lastUpdatedDate'.

  Args:
    query: Search query string
    limit: Maximum number of results to return
    sort_by: 'relevance', 'submittedDate', or 'lastUpdatedDate'

  Returns:
    List of paper dicts with metadata
  """
  params = {"search_query": query, "start": 0, "max_results": limit}
  if sort_by:
    params["sortBy"] = sort_by

  url = _build_query_url(params)
  return _fetch_and_parse(url)


def search_by_author(
    author_name: str,
    limit: int = 20,
) -> list[dict]:
  """Find papers by author name.

  Searches using the au: prefix. Accepts full names or partial names.

  Args:
    author_name: Author name to search for
    limit: Maximum number of results to return

  Returns:
    List of paper dicts with metadata
  """
  # Escape any double quotes in the author name
  safe_name = author_name.replace('"', '\\"')
  query = f'au:"{safe_name}"'
  return search_papers(query, limit=limit)


def search_by_category(
    category: str,
    limit: int = 50,
) -> list[dict]:
  """List new submissions in a category.

  Searches using the cat: prefix and sorts by submittedDate descending
  to return the most recent submissions.

  Args:
    category: arXiv category (e.g. 'cs.CL', 'cs.AI', 'q-bio.GN')
    limit: Maximum number of results to return

  Returns:
    List of paper dicts with metadata
  """
  query = f'cat:{category}'
  return search_papers(query, limit=limit, sort_by="submittedDate")


def get_paper(arxiv_id: str) -> dict:
  """Get paper metadata by arXiv ID.

  Accepts full arXiv IDs (e.g. '2305.10601', '2305.10601v1').

  Args:
    arxiv_id: The arXiv ID of the paper

  Returns:
    Paper dict with metadata, or dict with 'error' key if not found
  """
  params = {"id_list": arxiv_id, "start": 0, "max_results": 1}
  url = _build_query_url(params)

  papers = _fetch_and_parse(url)
  if not papers:
    return {"error": f"Paper not found: {arxiv_id}", "endpoint": "query"}
  return papers[0]


def get_paper_pdf_url(arxiv_id: str) -> dict:
  """Get the PDF download URL for a paper.

  Args:
    arxiv_id: The arXiv ID of the paper

  Returns:
    Dict with 'arxiv_id' and 'pdf_url' keys, or dict with 'error' key
  """
  paper = get_paper(arxiv_id)
  if isinstance(paper, dict) and "error" in paper:
    return paper
  pdf_url = paper.get("pdf_url")
  if not pdf_url:
    # Construct the standard PDF URL from the ID
    base_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
    pdf_url = f"https://arxiv.org/pdf/{base_id}.pdf"
  return {"arxiv_id": arxiv_id, "pdf_url": pdf_url}


def get_paper_source_url(arxiv_id: str) -> dict:
  """Get the source (.tar.gz) download URL for a paper.

  Args:
    arxiv_id: The arXiv ID of the paper

  Returns:
    Dict with 'arxiv_id' and 'source_url' keys, or dict with 'error' key
  """
  base_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
  source_url = f"https://arxiv.org/e-print/{base_id}"
  return {"arxiv_id": arxiv_id, "source_url": source_url}


def get_multiple_papers(ids: list[str]) -> list[dict]:
  """Get metadata for multiple papers at once by arXiv IDs.

  Args:
    ids: List of arXiv IDs (comma-separated string)

  Returns:
    List of paper dicts with metadata
  """
  ids_str = ",".join(ids)
  params = {"id_list": ids_str, "start": 0, "max_results": len(ids)}
  url = _build_query_url(params)
  return _fetch_and_parse(url)


def list_categories() -> list[dict]:
  """List all arXiv categories with descriptions.

  Returns a curated list of arXiv subject categories organized by area
  (Computer Science, Mathematics, Physics, etc.).

  Returns:
    List of dicts with 'id', 'description', and 'group' keys
  """
  # arXiv category definitions (major categories from arXiv.org)
  categories = [
      # Computer Science
      {"id": "cs.AI", "description": "Artificial Intelligence", "group": "Computer Science"},
      {"id": "cs.AR", "description": "Hardware Architecture", "group": "Computer Science"},
      {"id": "cs.CC", "description": "Computational Complexity", "group": "Computer Science"},
      {"id": "cs.CE", "description": "Computational Engineering, Finance, and Science", "group": "Computer Science"},
      {"id": "cs.CG", "description": "Computational Geometry", "group": "Computer Science"},
      {"id": "cs.CL", "description": "Computation and Language", "group": "Computer Science"},
      {"id": "cs.CR", "description": "Cryptography and Security", "group": "Computer Science"},
      {"id": "cs.CV", "description": "Computer Vision and Pattern Recognition", "group": "Computer Science"},
      {"id": "cs.CY", "description": "Computers and Society", "group": "Computer Science"},
      {"id": "cs.DB", "description": "Databases", "group": "Computer Science"},
      {"id": "cs.DC", "description": "Distributed, Parallel, and Cluster Computing", "group": "Computer Science"},
      {"id": "cs.DL", "description": "Digital Libraries", "group": "Computer Science"},
      {"id": "cs.DS", "description": "Data Structures and Algorithms", "group": "Computer Science"},
      {"id": "cs.ET", "description": "Emerging Technologies", "group": "Computer Science"},
      {"id": "cs.FL", "description": "Formal Languages and Automata Theory", "group": "Computer Science"},
      {"id": "cs.GL", "description": "General Literature", "group": "Computer Science"},
      {"id": "cs.GR", "description": "Graphics", "group": "Computer Science"},
      {"id": "cs.GT", "description": "Computer Science and Game Theory", "group": "Computer Science"},
      {"id": "cs.HC", "description": "Human-Computer Interaction", "group": "Computer Science"},
      {"id": "cs.IR", "description": "Information Retrieval", "group": "Computer Science"},
      {"id": "cs.IT", "description": "Information Theory", "group": "Computer Science"},
      {"id": "cs.LG", "description": "Machine Learning", "group": "Computer Science"},
      {"id": "cs.LO", "description": "Logic in Computer Science", "group": "Computer Science"},
      {"id": "cs.MA", "description": "Multiagent Systems", "group": "Computer Science"},
      {"id": "cs.MM", "description": "Multimedia", "group": "Computer Science"},
      {"id": "cs.MS", "description": "Mathematical Software", "group": "Computer Science"},
      {"id": "cs.NA", "description": "Numerical Analysis", "group": "Computer Science"},
      {"id": "cs.NE", "description": "Neural and Evolutionary Computing", "group": "Computer Science"},
      {"id": "cs.NI", "description": "Networking and Internet Architecture", "group": "Computer Science"},
      {"id": "cs.OH", "description": "Other Computer Science", "group": "Computer Science"},
      {"id": "cs.OS", "description": "Operating Systems", "group": "Computer Science"},
      {"id": "cs.PF", "description": "Performance", "group": "Computer Science"},
      {"id": "cs.PL", "description": "Programming Languages", "group": "Computer Science"},
      {"id": "cs.RO", "description": "Robotics", "group": "Computer Science"},
      {"id": "cs.SC", "description": "Symbolic Computation", "group": "Computer Science"},
      {"id": "cs.SD", "description": "Sound", "group": "Computer Science"},
      {"id": "cs.SE", "description": "Software Engineering", "group": "Computer Science"},
      {"id": "cs.SI", "description": "Social and Information Networks", "group": "Computer Science"},
      {"id": "cs.SY", "description": "Systems and Control", "group": "Computer Science"},
      # Mathematics
      {"id": "math.AG", "description": "Algebraic Geometry", "group": "Mathematics"},
      {"id": "math.AP", "description": "Analysis of PDEs", "group": "Mathematics"},
      {"id": "math.CO", "description": "Combinatorics", "group": "Mathematics"},
      {"id": "math.CT", "description": "Category Theory", "group": "Mathematics"},
      {"id": "math.DG", "description": "Differential Geometry", "group": "Mathematics"},
      {"id": "math.DS", "description": "Dynamical Systems", "group": "Mathematics"},
      {"id": "math.FA", "description": "Functional Analysis", "group": "Mathematics"},
      {"id": "math.GM", "description": "General Mathematics", "group": "Mathematics"},
      {"id": "math.GN", "description": "General Topology", "group": "Mathematics"},
      {"id": "math.GR", "description": "Group Theory", "group": "Mathematics"},
      {"id": "math.GT", "description": "Geometric Topology", "group": "Mathematics"},
      {"id": "math.HO", "description": "History and Overview", "group": "Mathematics"},
      {"id": "math.IT", "description": "Information Theory", "group": "Mathematics"},
      {"id": "math.KT", "description": "K-Theory and Homology", "group": "Mathematics"},
      {"id": "math.LO", "description": "Logic", "group": "Mathematics"},
      {"id": "math.MG", "description": "Metric Geometry", "group": "Mathematics"},
      {"id": "math.MP", "description": "Mathematical Physics", "group": "Mathematics"},
      {"id": "math.NA", "description": "Numerical Analysis", "group": "Mathematics"},
      {"id": "math.NT", "description": "Number Theory", "group": "Mathematics"},
      {"id": "math.OA", "description": "Operator Algebras", "group": "Mathematics"},
      {"id": "math.OC", "description": "Optimization and Control", "group": "Mathematics"},
      {"id": "math.PR", "description": "Probability", "group": "Mathematics"},
      {"id": "math.QA", "description": "Quantum Algebra", "group": "Mathematics"},
      {"id": "math.RA", "description": "Rings and Algebras", "group": "Mathematics"},
      {"id": "math.RT", "description": "Representation Theory", "group": "Mathematics"},
      {"id": "math.SG", "description": "Symplectic Geometry", "group": "Mathematics"},
      {"id": "math.SP", "description": "Spectral Theory", "group": "Mathematics"},
      {"id": "math.ST", "description": "Statistics Theory", "group": "Mathematics"},
      {"id": "math-ph", "description": "Mathematical Physics", "group": "Mathematics"},
      # Physics
      {"id": "astro-ph.CO", "description": "Cosmology and Nongalactic Astrophysics", "group": "Physics"},
      {"id": "astro-ph.EP", "description": "Earth and Planetary Astrophysics", "group": "Physics"},
      {"id": "astro-ph.GA", "description": "Astrophysics of Galaxies", "group": "Physics"},
      {"id": "astro-ph.HE", "description": "High Energy Astrophysical Phenomena", "group": "Physics"},
      {"id": "astro-ph.IM", "description": "Instrumentation and Methods for Astrophysics", "group": "Physics"},
      {"id": "astro-ph.SR", "description": "Solar and Stellar Astrophysics", "group": "Physics"},
      {"id": "cond-mat.dis-nn", "description": "Disordered Systems and Neural Networks", "group": "Physics"},
      {"id": "cond-mat.mes-hall", "description": "Mesoscale and Nanoscale Physics", "group": "Physics"},
      {"id": "cond-mat.mtrl-sci", "description": "Materials Science", "group": "Physics"},
      {"id": "cond-mat.other", "description": "Other Condensed Matter", "group": "Physics"},
      {"id": "cond-mat.quant-gas", "description": "Quantum Gases", "group": "Physics"},
      {"id": "cond-mat.soft", "description": "Soft Condensed Matter", "group": "Physics"},
      {"id": "cond-mat.stat-mech", "description": "Statistical Mechanics", "group": "Physics"},
      {"id": "cond-mat.str-el", "description": "Strongly Correlated Electrons", "group": "Physics"},
      {"id": "cond-mat.supr-con", "description": "Superconductivity", "group": "Physics"},
      {"id": "gr-qc", "description": "General Relativity and Quantum Cosmology", "group": "Physics"},
      {"id": "hep-ex", "description": "High Energy Physics - Experiment", "group": "Physics"},
      {"id": "hep-lat", "description": "High Energy Physics - Lattice", "group": "Physics"},
      {"id": "hep-ph", "description": "High Energy Physics - Phenomenology", "group": "Physics"},
      {"id": "hep-th", "description": "High Energy Physics - Theory", "group": "Physics"},
      {"id": "nucl-ex", "description": "Nuclear Experiment", "group": "Physics"},
      {"id": "nucl-th", "description": "Nuclear Theory", "group": "Physics"},
      {"id": "physics.acc-ph", "description": "Accelerator Physics", "group": "Physics"},
      {"id": "physics.ao-ph", "description": "Atmospheric and Oceanic Physics", "group": "Physics"},
      {"id": "physics.app-ph", "description": "Applied Physics", "group": "Physics"},
      {"id": "physics.atm-clus", "description": "Atomic and Molecular Clusters", "group": "Physics"},
      {"id": "physics.atom-ph", "description": "Atomic Physics", "group": "Physics"},
      {"id": "physics.bio-ph", "description": "Biological Physics", "group": "Physics"},
      {"id": "physics.chem-ph", "description": "Chemical Physics", "group": "Physics"},
      {"id": "physics.class-ph", "description": "Classical Physics", "group": "Physics"},
      {"id": "physics.comp-ph", "description": "Computational Physics", "group": "Physics"},
      {"id": "physics.data-an", "description": "Data Analysis, Statistics and Probability", "group": "Physics"},
      {"id": "physics.ed-ph", "description": "Physics Education", "group": "Physics"},
      {"id": "physics.flu-dyn", "description": "Fluid Dynamics", "group": "Physics"},
      {"id": "physics.gen-ph", "description": "General Physics", "group": "Physics"},
      {"id": "physics.geo-ph", "description": "Geophysics", "group": "Physics"},
      {"id": "physics.hist-ph", "description": "History and Philosophy of Physics", "group": "Physics"},
      {"id": "physics.ins-det", "description": "Instrumentation and Detectors", "group": "Physics"},
      {"id": "physics.med-ph", "description": "Medical Physics", "group": "Physics"},
      {"id": "physics.optics", "description": "Optics", "group": "Physics"},
      {"id": "physics.plasm-ph", "description": "Plasma Physics", "group": "Physics"},
      {"id": "physics.pop-ph", "description": "Popular Physics", "group": "Physics"},
      {"id": "physics.soc-ph", "description": "Physics and Society", "group": "Physics"},
      {"id": "physics.space-ph", "description": "Space Physics", "group": "Physics"},
      {"id": "quant-ph", "description": "Quantum Physics", "group": "Physics"},
      # Quantitative Biology
      {"id": "q-bio.BM", "description": "Biomolecules", "group": "Quantitative Biology"},
      {"id": "q-bio.CB", "description": "Cell Behavior", "group": "Quantitative Biology"},
      {"id": "q-bio.GN", "description": "Genomics", "group": "Quantitative Biology"},
      {"id": "q-bio.MN", "description": "Molecular Networks", "group": "Quantitative Biology"},
      {"id": "q-bio.NC", "description": "Neurons and Cognition", "group": "Quantitative Biology"},
      {"id": "q-bio.OT", "description": "Other Quantitative Biology", "group": "Quantitative Biology"},
      {"id": "q-bio.PE", "description": "Populations and Evolution", "group": "Quantitative Biology"},
      {"id": "q-bio.QM", "description": "Quantitative Methods", "group": "Quantitative Biology"},
      {"id": "q-bio.SC", "description": "Subcellular Processes", "group": "Quantitative Biology"},
      {"id": "q-bio.TO", "description": "Tissues and Organs", "group": "Quantitative Biology"},
      # Quantitative Finance
      {"id": "q-fin.CP", "description": "Computational Finance", "group": "Quantitative Finance"},
      {"id": "q-fin.EC", "description": "Economics", "group": "Quantitative Finance"},
      {"id": "q-fin.GN", "description": "General Finance", "group": "Quantitative Finance"},
      {"id": "q-fin.MF", "description": "Mathematical Finance", "group": "Quantitative Finance"},
      {"id": "q-fin.PM", "description": "Portfolio Management", "group": "Quantitative Finance"},
      {"id": "q-fin.PR", "description": "Pricing of Securities", "group": "Quantitative Finance"},
      {"id": "q-fin.RM", "description": "Risk Management", "group": "Quantitative Finance"},
      {"id": "q-fin.ST", "description": "Statistical Finance", "group": "Quantitative Finance"},
      {"id": "q-fin.TR", "description": "Trading and Market Microstructure", "group": "Quantitative Finance"},
      # Statistics
      {"id": "stat.AP", "description": "Applications", "group": "Statistics"},
      {"id": "stat.CO", "description": "Computation", "group": "Statistics"},
      {"id": "stat.ME", "description": "Methodology", "group": "Statistics"},
      {"id": "stat.ML", "description": "Machine Learning", "group": "Statistics"},
      {"id": "stat.OT", "description": "Other Statistics", "group": "Statistics"},
      {"id": "stat.TH", "description": "Statistics Theory", "group": "Statistics"},
      # Electrical Engineering and Systems Science
      {"id": "eess.AS", "description": "Audio and Speech Processing", "group": "Electrical Engineering and Systems Science"},
      {"id": "eess.IV", "description": "Image and Video Processing", "group": "Electrical Engineering and Systems Science"},
      {"id": "eess.SP", "description": "Signal Processing", "group": "Electrical Engineering and Systems Science"},
      {"id": "eess.SY", "description": "Systems and Control", "group": "Electrical Engineering and Systems Science"},
      # Economics
      {"id": "econ.EM", "description": "Econometrics", "group": "Economics"},
      {"id": "econ.GN", "description": "General Economics", "group": "Economics"},
      {"id": "econ.TH", "description": "Theoretical Economics", "group": "Economics"},
  ]
  return categories


def get_recent_papers(
    category: str | None = None,
    limit: int = 50,
) -> list[dict]:
  """Get most recent submissions, optionally filtered by category.

  Sorts by submittedDate descending.

  Args:
    category: Optional arXiv category to filter by (e.g. 'cs.CL', 'cs.AI')
    limit: Maximum number of results to return

  Returns:
    List of paper dicts with metadata
  """
  if category:
    query = f'cat:{category}'
  else:
    query = 'all:*'
  return search_papers(query, limit=limit, sort_by="submittedDate")


# ---------------------------------------------------------------------------
# CLI dispatch — inferred from type hints via inspect
# ---------------------------------------------------------------------------
FUNCTIONS = {
    fn.__name__: fn
    for fn in [
        search_papers,
        search_by_author,
        search_by_category,
        get_paper,
        get_paper_pdf_url,
        get_paper_source_url,
        get_multiple_papers,
        list_categories,
        get_recent_papers,
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
    print("Usage: arxiv_api.py <output_file> <func> [--flag val]")
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
