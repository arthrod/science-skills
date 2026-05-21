# Science Skills

[![Install via skills.sh](https://img.shields.io/badge/skills.sh-install-green)](https://skills.sh/google-deepmind/science-skills)

A collection of agent skills for scientific research tasks, spanning genomics,
structural biology, cheminformatics, literature search, and more.

Each skill provides structured instructions, scripts, and resources that extend
an AI agent's capabilities for specialized scientific tasks.

## Skill Structure

Each skill directory contains:

-   **SKILL.md** — Main instruction file with YAML frontmatter and detailed
    markdown instructions
-   **scripts/** — Helper scripts and utilities
-   **references/** — Additional documentation and references (optional)

## Getting started with GDM Science Skills

Install the Science Skills bundle via
[npx](https://docs.npmjs.com/cli/commands/npx) using:

```bash
npx skills add google-deepmind/science-skills/
```

## Using science skills with [Google Antigravity](https://antigravity.google/)

If you're a new Google Antigravity user:

-   Launch the application after downloading Google Antigravity and check the
    box for Science at the 'Build with Google' step - this will install the
    curated collection of our Science Skills.

If you're an existing Google Antigravity user:

-   Update to the latest version then open Settings -> Customizations -> Build
    with Google Plugins (click on 'Customize' at the bottom of the page) ->
    Download the `Science` plugin

### Prerequisites

We use the `uv` package manager to handle dependencies. The first time you
trigger a Science Skill, the agent will ask for approval and install `uv`, and
then proceed to respond to your scientific query / task. We recommend restarting
Antigravity after this first time installation.

Some skills, such as AlphaGenome and OpenAlex, require an API key to function.
Others, such as ClinVar, benefit from an API key to unlock higher rate limits
but are still functional without one. The agent should prompt you to obtain the
API key and guide you through writing in the correct location. However, if you
would rather do this yourself, you can run a command like this in your terminal:
`echo "ALPHAGENOME_API_KEY=your_actual_api_key" >> ~/.env`

## Links

You can find examples of Science Skills use cases, including a demo, at
[antigravity.google/use-cases/science](https://antigravity.google/use-cases/science).

We have also published a
[technical report](https://storage.googleapis.com/deepmind-media/papers/google_deepmind_science_skills_for_antigravity_towards_efficient_and_reliable_scientific_workflows.pdf)
on the Science Skills.

## Skills

The repository currently contains the following skills:

### Science & Bioinformatics
- `pubchem-database` — Query PubChem, search by name/CID/SMILES, retrieve chemical properties, and perform similarity/substructure searches for cheminformatics.
- `alphafold-database-fetch-and-analyze` — Retrieve and analyze AlphaFold predicted protein structures with confidence metrics (pLDDT), domain boundaries, and disorder assessment.
- `alphagenome-single-variant-analysis` — Analyze non-coding genetic variant effects on gene expression, chromatin accessibility, and histone marks via the AlphaGenome API.
- `chembl-database` — Query ChEMBL for bioactive molecules, drug targets, bioactivity data, approved drugs, and chemical structures.
- `clinical-trials-database` — Search ClinicalTrials.gov for trials by condition, drug, location, status, and phase; retrieve NCT details and eligibility criteria.
- `clinvar-database` — Query NCBI ClinVar for clinical significance, pathogenicity classifications, and evidence for human genomic variants.
- `dbsnp-database` — Look up, map, and search short genetic variants (SNPs, indels) in NCBI's dbSNP database.
- `embl-ebi-ols` — Query the EMBL-EBI Ontology Lookup Service for biomedical ontology terms across 250+ ontologies (GO, DOID, HP, etc.).
- `encode-ccres-database` — Query the ENCODE Registry of cis-Regulatory Elements (cCREs) via the SCREEN GraphQL API.
- `ensembl-database` — Query Ensembl for gene/transcript/protein ID resolution, genomic sequences, gene structures, and variant effect prediction.
- `foldseek-structural-search` — Perform 3D structural similarity searches of proteins against PDB, AlphaFold, CATH, and other databases.
- `gnomad-database` — Query gnomAD for allele frequencies, gene constraint metrics (pLI, LOEUF), and variant rarity across populations.
- `gtex-database` — Retrieve quantitative RNA expression data and eQTL information from the GTEx Project across 54 non-diseased tissue sites.
- `human-protein-atlas-database` — Retrieve semi-quantitative protein expression and spatial localization data from the Human Protein Atlas.
- `interpro-database` — Identify protein domains, families, and sites; explore species distribution and annotate genomes with protein families and GO terms.
- `jaspar-database` — Query JASPAR for Transcription Factor binding profiles, Position Frequency Matrices (PFMs), and matrix metadata.
- `ncbi-sequence-fetch` — Retrieve protein and nucleotide sequences from NCBI databases using E-utilities (accession, gene, organism, PubMed ID).
- `openfda-database` — Query the openFDA API for drug/device/food adverse events, recalls, labeling, approvals, and regulatory data.
- `opentargets-database` — Query Open Targets for target-disease associations, drug target discovery, tractability, and genetics evidence.
- `pdb-database` — Search and download experimentally-determined 3D biomolecular structures from the Protein Data Bank.
- `protein-sequence-msa` — Perform multiple sequence alignment of proteins using EBI Clustal Omega.
- `protein-sequence-similarity-search` — Search for homologous protein sequences using MMseqs2 or BLAST.
- `pubmed-database` — Search PubMed for scientific literature, abstracts, and full text; link papers to biological databases.
- `quickgo-database` — Query QuickGO and the Gene Ontology for biological processes, molecular functions, and cellular components.
- `reactome-database` — Query Reactome for pathway analysis, gene list enrichment, and reaction participant data.
- `string-database` — Query STRING for protein-protein interactions, functional enrichment, and homology data.
- `ucsc-conservation-and-tfbs` — Fetch evolutionary conservation scores (phyloP, phastCons) and TF binding sites from the UCSC Genome Browser.
- `unibind-database` — Query UniBind for experimentally validated transcription factor binding site datasets.
- `uniprot-database` — Access protein metadata, function, taxonomy, and sequences across UniProtKB, UniParc, and UniRef.
- `pymol` — Visualize, analyze, and render protein and molecular structures using PyMOL.
- `acl-anthology` — Search NLP research literature via the ACL Anthology and PapersWithCode API across top NLP venues.

### Research & Literature
- `semantic-scholar` — Search and retrieve academic papers from the Semantic Scholar corpus with citation graph, recommendations, embeddings, and TLDR summaries.
- `crossref` — Query Crossref for DOI metadata, references, funding information, journals, and funder data across all academic disciplines.
- `arxiv` — Search and retrieve papers from arXiv (CS, physics, math, biology, finance).
- `papers-with-code` — Find papers with code repositories, evaluation results, tasks, benchmarks, and SOTA leaderboards.
- `huggingface-datasets` — Search and discover datasets on the Hugging Face Hub with filtering by task, language, and tags.
- `open-review` — Access OpenReview conference proceedings, reviews, and peer review content.
- `literature-search-arxiv` — Search and retrieve scientific preprints from arXiv with full-text download capabilities.
- `literature-search-biorxiv` — Browse and filter life sciences preprints from bioRxiv and medRxiv.
- `literature-search-europepmc` — Search Europe PMC for scientific literature and download open-access full texts and PDFs.
- `literature-search-openalex` — Query OpenAlex for research papers, authors, institutions, topics, sources, publishers, and bibliometric data.

### Legal Research
- `courtlistener` — Search US federal and state court opinions, dockets, judges, and oral arguments via the CourtListener API (Free Law Project).
- `legislation-gov-uk` — Access UK legislation including Acts, Statutory Instruments, amendments, and historical versions.
- `oyez` — Access US Supreme Court case metadata, oral argument transcripts, and justice biographies via the Oyez Project.

### Economics & Government Data
- `fred` — Access 800,000+ US and international economic time series from the Federal Reserve Bank of St. Louis (GDP, inflation, employment, interest rates, etc.).
- `world-bank` — Query global development indicators (GDP, population, education, health) for 200+ countries.
- `data-gov` — Search and access 300,000+ US federal open datasets.

## Licensing & Disclaimer

Copyright 2026 Google LLC

All software is licensed under the Apache License, Version 2.0 (Apache 2.0); you
may not use this file except in compliance with the Apache 2.0 license. You may
obtain a copy of the Apache 2.0 license at:
https://www.apache.org/licenses/LICENSE-2.0

As set out in the attached file
‘[Skill Licences and Terms of Use](SKILL_LICENSES.md)’ certain third party data
sources referenced within individual Skill files have their own applicable
licenses and/or terms of use. See the
‘[Skill Licences and Terms of Use](SKILL_LICENSES.md)’ file for more
information. You are responsible for ensuring that your use of individual Skill
files complies with any such applicable licenses/ terms of use.

All other materials are licensed under the Creative Commons Attribution 4.0
International License (CC-BY). You may obtain a copy of the CC-BY license at:
https://creativecommons.org/licenses/by/4.0/legalcode

Unless required by applicable law or agreed to in writing, all software and
materials distributed here under the Apache 2.0 or CC-BY licenses are
distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied. See the licenses for the specific language governing
permissions and limitations under those licenses.

This is not an official Google product.
