# Mappa delle skill scientifiche

> Documento generato da `tools/mappa-skill-scientifiche.py` leggendo una copia locale di `K-Dense-AI/scientific-agent-skills`. Non si scrive a mano: si rigenera. Le tre colonne che contano sono l'autore, la licenza e la presenza di programmi eseguibili, perché sono i tre criteri che l'avviso di sicurezza della raccolta chiede di guardare prima di installare.

## In breve

Sono 166 skill. Ne ha scritte 136 la casa che mantiene la raccolta e 30 altri autori, e la differenza è dichiarata a monte come differenza di profondità della revisione. Ne portano programmi eseguibili 106, cioè la maggioranza, ed è la classe per cui vale passare uno scanner prima di installare. Ne hanno licenza proprietaria 5, dentro una raccolta che si presenta come MIT. E 27 coprono un terreno che un pacchetto di questo sistema già copre.

| Licenza | Skill |
|---|---|
| MIT | 102 |
| Apache-2.0 | 19 |
| BSD-3-Clause | 16 |
| Proprietaria | 5 |
| (non dichiarata) | 4 |
| Unknown | 3 |
| https://creativecommons.org/licenses/by/4.0/ | 1 |
| Biopython License Agreement | 1 |
| GPLv3 | 1 |
| GPL-2.0 | 1 |
| PolyForm-Noncommercial-1.0.0 | 1 |
| BSD | 1 |
| CC-BY-4.0 | 1 |
| GPL-3.0-or-later | 1 |
| BSD-2-Clause | 1 |
| This skill is provided under the MIT License. IDC data itself has individual licensing (mostly CC-BY, some CC-NC) that must be respected when using the data. | 1 |
| https://github.com/matplotlib/matplotlib/tree/main/LICENSE | 1 |
| 3-clause BSD | 1 |
| https://github.com/pola-rs/polars/blob/main/LICENSE | 1 |
| Apache License, Version 2.0 | 1 |
| 3 clause BSD | 1 |
| https://github.com/sympy/sympy/blob/master/LICENSE | 1 |
| CC BY-NC-SA 4.0 | 1 |

Gli autori diversi dalla casa, con quante skill ciascuno: Kuan-lin Huang (5), Anthropic, PBC (4), AHK Strategies (ashrafkahoush-ux) (3), Clayton Young / Superior Byte Works, LLC (@borealBytes) (2), BGPT (1), Yaroslav Halchenko (1), Dylan Pulver (1), Ratschlab, ETH Zurich (1), Exa (1), Helena Bioinformatics (1), Genomic Intelligence (1), Andrey Fedorov, @fedorov (1), neuroepithelial (1), Dnaerys (1), OpenPIV Team (1), Beifang Niu (1), Paperzilla Inc (1), Rowan Science (1), Tamarind Bio (1), Jeremy Leipzig (1).

## I settori, come li dichiara la raccolta

Sono la tassonomia di chi la mantiene, letta dal suo README e non inventata qui. Servono al gate dei pacchetti per capire quale porzione della raccolta riguardi un progetto: quasi sempre è una sola riga di questa tabella.

| Settore | Skill dichiarate |
|---|---|
| Bioinformatics & Genomics | 28 |
| Cheminformatics & Drug Discovery | 10 |
| Proteomics & Mass Spectrometry | 2 |
| Clinical Research & Evidence Workflows | 8 |
| Preclinical Research & Animal Welfare | 1 |
| Medical Imaging & Digital Pathology | 4 |
| Neuroscience & Electrophysiology | 3 |
| Materials Science, Chemistry & Physics | 7 |
| Engineering & Simulation | 6 |
| Data Analysis & Visualization | 22 |
| Laboratory Automation | 6 |
| Multi-omics & Systems Biology | 3 |
| Protein Engineering & Design | 4 |
| Scientific Communication | 27 |
| Infrastructure & Platforms | 12 |
| Research Methodology & Planning | 13 |
| Regulatory & Standards | 2 |

Le categorie dichiarano 158 skill in totale contro le 166 presenti sul disco. Lo scarto non è un errore di questo programma: le categorie del README si sovrappongono e alcune skill vi compaiono due volte o nessuna. Va letto come indicazione della grandezza di un settore, non come conteggio.

## Le skill che questo sistema copre già

Righe da non prendere senza avere deciso quale delle due capacità resta in uso, e da registrare come decisione quando si prende comunque quella di là.

| Skill | Che cosa in questo sistema copre già lo stesso terreno |
|---|---|
| `bgpt-paper-search` | academic-researcher, semantic-scholar-mcp |
| `citation-management` | book-bib-extract, zotero-mcp, refchecker-mcp |
| `docx` | doc-ingest, docx-to-docs |
| `exa-search` | notebooklm-bridge |
| `infographics` | la skill nativa dataviz |
| `latex-posters` | latex |
| `liteparse` | doc-ingest |
| `literature-review` | academic-researcher, notebooklm-bridge |
| `markdown-mermaid-writing` | diagrams |
| `markitdown` | doc-ingest |
| `matplotlib` | la skill nativa dataviz |
| `open-notebook` | knowledge-wiki, operations-log |
| `paper-lookup` | academic-researcher, arxiv-cli, academix |
| `paperclip` | academic-researcher, paperqa2 |
| `paperzilla` | academic-researcher, paperqa2 |
| `pdf` | doc-ingest, book-to-skill |
| `peer-review` | academic-researcher |
| `pptx` | doc-ingest |
| `pyzotero` | zotero-mcp |
| `research-lookup` | academic-researcher, academix |
| `scholar-evaluation` | academic-researcher |
| `scientific-schematics` | diagrams |
| `scientific-visualization` | la skill nativa dataviz |
| `scientific-writing` | interaction-style.md, humanizer |
| `seaborn` | la skill nativa dataviz |
| `venue-templates` | latex |
| `xlsx` | doc-ingest |

## Tutte le skill

La colonna del codice dice se la skill porta una cartella `scripts/` con programmi eseguibili. La colonna dell'autore dice soltanto se sia della casa: e lo fa secondo il criterio che la raccolta stessa indica per sapere quanta revisione quella skill abbia avuto.

| Skill | Autore | Licenza | Codice | Che cosa fa |
|---|---|---|---|---|
| `adaptyv` | casa | MIT | no | How to use the Adaptyv Bio Foundry API and Python SDK for protein experiment design, submission, and results retrieval. Use this skill whenever the user mentions Adaptyv, Foundry API, protein binding assays, protein screening... |
| `aeon` | casa | BSD-3-Clause | no | This skill should be used for time series machine learning tasks including classification, regression, clustering, forecasting, anomaly detection, segmentation, and similarity search. Use when working with temporal data, sequential... |
| `alphagenome` | casa | MIT | si | Look up precomputed AlphaGenome Atlas effects for any GRCh38 single-nucleotide variant (AVI score with Phred and 18 SHAP feature attributions, plus raw and quantile scores for RNA-seq, DNase, ATAC, ChIP-TF, ChIP-histone, CAGE, PRO-cap,... |
| `analytical-method-validation` | casa | MIT | si | Plan, execute, and document validation, verification, and transfer of analytical procedures under the governing framework - ICH Q2(R2) and Q14, USP <1220>/<1225>/<1226>, ICH M10 bioanalytical, CLSI EP, or ISO/IEC 17025. Use for HPLC,... |
| `anndata` | casa | BSD-3-Clause | no | Data structure for annotated matrices in single-cell analysis. Use when working with .h5ad files or integrating with the scverse ecosystem. This is the data format skill—for analysis workflows use scanpy; for probabilistic models use... |
| `arbor` | casa | MIT | si | Autonomously improve a real artifact (code, training recipe, agent harness, data pipeline, prompt) against an objective and an evaluator, using Hypothesis Tree Refinement (HTR) from the Arbor paper. Use this whenever someone wants to... |
| `arboreto` | casa | BSD-3-Clause | si | Infer gene regulatory networks (GRNs) from gene expression data using scalable algorithms (GRNBoost2, GENIE3). Use when analyzing transcriptomics data (bulk RNA-seq, single-cell RNA-seq) to identify transcription factor-target gene... |
| `astropy` | casa | BSD-3-Clause | no | Core Python library for astronomy and astrophysics workflows that need Astropy APIs, including units/quantities, coordinates, FITS I/O, tables, time systems, WCS, and cosmology. Use when implementing or debugging astronomical data... |
| `autoskill` | casa | MIT | si | Observe the user's screen via screenpipe, detect repeated research workflows, match them against existing scientific-agent-skills, and draft new skills (or composition recipes that chain existing ones) for the patterns not yet covered.... |
| `benchling-integration` | casa | MIT | no | Benchling Python SDK and REST API integration for registry entities, inventory, ELN entries, workflows, Benchling Apps, and Data Warehouse queries. Use when automating lab data with benchling-sdk or the v2 API. |
| `bgpt-paper-search` | BGPT | MIT | no | Search scientific papers and retrieve structured experimental data extracted from full-text studies via the BGPT MCP server. Returns 25+ fields per paper including methods, results, sample sizes, quality scores, and conclusions. Use for... |
| `bids` | Yaroslav Halchenko | https://creativecommons.org/licenses/by/4.0/ | si | > |
| `biopython` | casa | Biopython License Agreement | no | Comprehensive molecular biology toolkit. Use for sequence manipulation, file parsing (FASTA/GenBank/PDB), phylogenetics, and programmatic NCBI/PubMed access (Bio.Entrez). Best for batch processing, custom bioinformatics pipelines, BLAST... |
| `bioservices` | casa | GPLv3 | si | Unified Python interface to 40+ bioinformatics services. Use when querying multiple databases (UniProt, KEGG, ChEMBL, Reactome) in a single workflow with consistent API. Best for cross-database analysis, ID mapping across services. For... |
| `bulk-rnaseq` | casa | MIT | si | End-to-end bulk RNA-seq orchestrator — takes raw FASTQ reads through QC and trimming (FastQC, fastp/Trim Galore), alignment and quantification (STAR, Salmon, featureCounts), assembles a gene-level counts matrix, then hands off to... |
| `cellxgene-census` | casa | MIT | no | Query the CZ CELLxGENE Census programmatically for versioned public single-cell and spatial transcriptomics data. Use when you need population-scale cell metadata, gene expression slices, Census summary counts, source H5AD... |
| `cirq` | casa | Apache-2.0 | no | Google quantum computing framework. Use when targeting Google Quantum AI hardware, designing noise-aware circuits, or running quantum characterization experiments. Best for Google hardware, noise modeling, and low-level circuit design.... |
| `citation-management` | casa | MIT | si | Comprehensive citation management for academic research. Search OpenAlex, PubMed, and Google Scholar for papers, extract accurate metadata, validate citations, and generate properly formatted BibTeX entries. This skill should be used... |
| `clinical-decision-support` | casa | MIT | si | Prepare and validate research-only clinical decision-support evaluation, evidence-profile, cohort, survival, biomarker/model, privacy, and governance artifacts. Use for aggregate or synthetic research documentation and traceability—not... |
| `clinical-reports` | casa | MIT | si | Create safety-bounded draft structures and run local deterministic checks for clinical case, diagnostic, trial, safety, and aggregate research reports. Use only with synthetic, de-identified, or aggregate inputs and verified source-fact... |
| `cobrapy` | casa | GPL-2.0 | no | Constraint-based metabolic modeling (COBRA). FBA, FVA, gene knockouts, flux sampling, SBML models, for systems biology and metabolic engineering analysis. |
| `consciousness-council` | AHK Strategies (ashrafkahoush-ux) | MIT | no | Run a multi-perspective Mind Council deliberation on any question, decision, or creative challenge. Use this skill whenever the user wants diverse viewpoints, needs help making a tough decision, asks for a council/panel/board... |
| `dask` | casa | BSD-3-Clause | no | Distributed computing for larger-than-RAM pandas/NumPy workflows. Use when you need to scale existing pandas/NumPy code beyond memory or across clusters. Best for parallel file processing, distributed ML, integration with existing... |
| `database-lookup` | casa | MIT | no | Query documented public database APIs with explicit endpoints, filters, pagination, and provenance. Use when a scientific, regulatory, financial, or other database-backed fact must be retrieved reproducibly from a named source rather... |
| `datalad` | Dylan Pulver | MIT | no | Retrieve, version, and publish scientific datasets with DataLad and git-annex, and capture computational provenance with datalad run, rerun, and containers-run. Use when cloning or fetching data from OpenNeuro, DANDI,... |
| `datamol` | casa | Apache-2.0 | no | Pythonic wrapper around RDKit with simplified interface and sensible defaults. Preferred for standard drug discovery including SMILES parsing, standardization, descriptors, fingerprints, clustering, 3D conformers, parallel processing.... |
| `deepchem` | casa | MIT | si | Molecular ML with diverse featurizers and pre-built datasets. Use for property prediction (ADMET, toxicity) with traditional ML or GNNs when you want extensive featurization options and MoleculeNet benchmarks. Best for quick experiments... |
| `deepspot-m` | Ratschlab, ETH Zurich | PolyForm-Noncommercial-1.0.0 | no | Generate transcriptome-wide virtual spatial transcriptomics from H&E histology with DeepSpot-M. Use when you need spatial gene expression in log1p-CPM for 224x224 tiles at about 20x, want to query protein-coding genes by symbol instead... |
| `deeptools` | casa | BSD | si | NGS analysis toolkit. BAM to bigWig conversion, QC (correlation, PCA, fingerprints), heatmaps/profiles (TSS, peaks), for ChIP-seq, RNA-seq, ATAC-seq visualization. |
| `depmap` | Kuan-lin Huang | CC-BY-4.0 | no | Query the Cancer Dependency Map (DepMap) for cancer cell line gene dependency scores (CRISPR Chronos), drug sensitivity data, and gene effect profiles. Use for identifying cancer-specific vulnerabilities, synthetic lethal interactions,... |
| `dhdna-profiler` | AHK Strategies (ashrafkahoush-ux) | MIT | no | Extract cognitive patterns and thinking fingerprints from any text. Use this skill when the user wants to analyze how someone thinks, understand cognitive style, profile writing or speech patterns, compare thinking styles between... |
| `diffdock` | casa | MIT | si | DiffDock and DiffDock-L molecular docking. Use for protein-small-molecule pose prediction from PDB or sequence plus SMILES/SDF/MOL2, batch docking, virtual screening, and pose-confidence interpretation. Not for binding affinity prediction. |
| `dnanexus-integration` | casa | MIT | si | Build and operate reproducible genomics workloads on DNAnexus with the dx CLI, dxpy, apps/applets, native workflows, dxCompiler, and Nextflow. Use for DNAnexus data transfers, dxapp.json development, execution monitoring, workflow... |
| `docx` | Anthropic, PBC | Proprietaria | si | Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files) or Word templates (.dotx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', '.dotx', or requests to... |
| `esm` | casa | MIT | no | Use when working directly with the `esm` Python SDK, ESM3 or ESMC model IDs, Forge/Biohub inference clients, or ESMFold2 folding workflows. |
| `etetoolkit` | casa | GPL-3.0-or-later | si | Analyze, manipulate, compare, annotate, and visualize phylogenetic or other hierarchical trees with ETE 4. Use for Newick/Nexus tree I/O, topology edits and pattern matching, Robinson-Foulds comparisons, gene-tree evolutionary events... |
| `exa-search` | Exa | MIT | si | Web toolkit powered by Exa, tuned for scientific and technical content. Use this skill when the user needs to search the web or fetch/extract URL content. Covers: web search (semantic lookups, research, current info — with optional... |
| `experimental-design` | casa | MIT | si | Design experiments and studies BEFORE data is collected — choosing a design, randomizing, blocking, and laying out treatment combinations so results are interpretable. Use whenever someone is planning a study, asks how to assign... |
| `exploratory-data-analysis` | casa | MIT | si | Perform bounded, local exploratory analysis of explicitly supported scientific files. Use for redacted CSV/TSV/JSON profiles; optional NumPy, HDF5, FASTA/FASTQ, and basic image metadata inspection; missingness/leakage audits; outlier... |
| `flowio` | casa | BSD-3-Clause | si | Read, inspect, and write Flow Cytometry Standard (FCS) 2.0, 3.0, and 3.1 files with FlowIO. Use for low-level FCS metadata and channel inspection, NumPy event extraction, multi-dataset files, table export, and FCS 3.1 creation; use... |
| `fluidsim` | casa | MIT | si | Plan, configure, inspect, restart, and analyze bounded FluidSim computational-fluid-dynamics simulations with explicit numerical-validity and HPC safety checks. Use for FluidSim solver selection, parameter review, FFT/MPI setup, output... |
| `folklore-variant-evidence` | Helena Bioinformatics | MIT | no | Retrieve ClinGen gene-disease validity assertions for a public gene or disease, and review source-linked public evidence and literature for one supported GRCh38 germline nuclear SNV or simple indel through Folklore Clinical Variant... |
| `generate-image` | casa | MIT | si | Generate or edit images with AI models through the OpenRouter Image API (Gemini, Seedream, Recraft, GPT-Image, Riverflow). Use for photos, illustrations, artwork, concept art, visual assets, logos, and image editing or compositing from... |
| `geniml` | casa | MIT | si | Use Geniml for audited local genomic-interval workflows: validate BED and universe contracts, plan Region2Vec or scEmbed runs, inspect model/tokenizer compatibility, and assess consensus universes. |
| `genomic-coordinates` | casa | MIT | si | Convert genomic intervals between coordinate conventions, normalise and compare variant representations, and detect assembly or contig-naming mismatches before they corrupt an analysis. Use whenever coordinates cross a format, tool, or... |
| `genomic-intelligence` | Genomic Intelligence | MIT | no | Predict regulatory features, gene structure, and expression directly from DNA sequence using Genomic Intelligence's hosted transformer DNA language models — no local GPU or model weights. Six tasks over a REST API and a hosted MCP... |
| `geomaster` | casa | MIT | no | Comprehensive geospatial science skill covering remote sensing, GIS, spatial analysis, machine learning for earth observation, and 30+ scientific domains. Supports satellite imagery processing (Sentinel, Landsat, MODIS, SAR,... |
| `geopandas` | casa | MIT | si | Guidance and local audit tools for Python workflows that directly use GeoPandas GeoSeries, GeoDataFrame, spatial operations, or vector-data I/O. |
| `get-available-resources` | casa | MIT | si | Detect host inventory and effective CPU, memory, disk, scheduler, container, and accelerator limits when a user asks for resource-aware planning or before a clearly resource-sensitive local workload. Produces a redacted JSON snapshot... |
| `gget` | casa | BSD-2-Clause | si | Fast CLI/Python queries to 20+ bioinformatics databases. Use for quick lookups: gene info, BLAST/BLAT, viral sequence downloads, AlphaFold structures, enrichment analysis, OpenTargets, COSMIC, CELLxGENE, and 8cube mouse... |
| `ginkgo-cloud-lab` | casa | MIT | no | Submit and manage protocols on Ginkgo Bioworks Cloud Lab (cloud.ginkgo.bio), a web-based interface for autonomous lab execution on Reconfigurable Automation Carts (RACs). Use when the user wants to run protein expression and... |
| `glycoengineering` | Kuan-lin Huang | Unknown | no | Analyze and engineer protein glycosylation. Scan sequences for N-glycosylation sequons (N-X-S/T), predict O-glycosylation hotspots, and access curated glycoengineering tools (NetOGlyc, GlycoShield, GlycoWorkbench). For glycoprotein... |
| `gtars` | casa | MIT | si | Use Gtars for local genomic interval models and set algebra, overlaps and counts, consensus and coverage, tokenization, fragment processing, and refget/BEDbase planning across Python, Rust, and the CLI. |
| `histolab` | casa | Apache-2.0 | no | Lightweight WSI tile extraction and preprocessing. Use for basic slide processing, tissue detection, tile extraction, and stain normalization for H&E images. Best for simple pipelines, dataset preparation, and quick tile-based analysis.... |
| `hugging-science` | casa | (non dichiarata) | si | Use when the user is doing AI/ML work in a scientific domain such as biology, chemistry, physics, astronomy, climate, genomics, materials, medicine, ecology, energy, engineering, math, drug discovery, protein design, weather modeling,... |
| `hypogenic` | casa | MIT | si | Plans and audits use of ChicagoHAI HypoGeniC/HypoRefine for LLM-assisted hypothesis generation from labeled text datasets. Use for the `hypogenic` package, its task configs, hypothesis banks, or HypoBench datasets—not for manual... |
| `hypothesis-generation` | casa | MIT | si | Formulate evidence-bounded scientific questions, candidate hypotheses, rival explanations, causal or associational claims, discriminating predictions, measurements, and preregistration-ready analysis plans. Use when turning observations... |
| `imaging-data-commons` | Andrey Fedorov, @fedorov | This skill is provided under the MIT License. IDC data itself has individual licensing (mostly CC-BY, some CC-NC) that must be respected when using the data. | si | Query and download public cancer imaging data from NCI Imaging Data Commons. Invoke for any question about IDC collections, cancer imaging datasets, DICOM data access, radiology (CT, MR, PET) or pathology AI training sets, metadata... |
| `infographics` | casa | (non dichiarata) | si | Create professional infographics using Nano Banana Pro AI with smart iterative refinement. Uses Gemini 3.6 Flash for quality review. Integrates research-lookup and web search for accurate data. Supports 10 infographic types, 8 industry... |
| `iso-standards-readiness` | casa | MIT | si | Prepares and structurally reviews readiness evidence for ISO management-system and laboratory-competence standards - ISO 13485 medical device QMS, ISO 14971 device risk management, ISO/IEC 17025 testing and calibration laboratories, and... |
| `lab-hardware-cad` | casa | MIT | si | Design custom laboratory hardware as parametric build123d models and export fabrication-ready STEP, STL, and DXF files - microfluidic chips and molds, optomechanical mounts and breadboard adapters, cuvette and microplate holders, tube... |
| `labarchive-integration` | casa | MIT | si | Securely integrate with the official LabArchives ELN REST-like API and Inventory API v1. Use for regional endpoint selection, signed-request construction, user authorization and UID flows, local LA container validation, and verified... |
| `lamindb` | casa | Apache-2.0 | no | Use when working with LaminDB, the open-source lineage-native lakehouse for biological datasets and models. Covers setup, artifact registration, query/search, lineage tracking, validation, ontology-backed annotation with Bionty,... |
| `latchbio-integration` | casa | MIT | si | Build, register, debug, and operate bioinformatics workflows on Latch using the Python SDK, CLI, Latch Data and Registry, Nextflow, Snakemake, programmatic execution, and Latch MCP. Use when authoring or deploying Latch workflows,... |
| `latex-posters` | casa | (non dichiarata) | si | Create professional research posters in LaTeX using beamerposter, tikzposter, or baposter. Support for conference presentations, academic posters, and scientific communication. Includes layout design, color schemes, multi-column... |
| `liteparse` | casa | Apache-2.0 | si | Local document and PDF parsing that returns spatial text with bounding boxes. Use for extracting text from PDFs, DOCX, Office files, and images; running OCR on scans; producing layout-preserved JSON for RAG; batch-ingesting folders of... |
| `literature-review` | casa | MIT | si | Conduct comprehensive, systematic literature reviews using multiple academic databases (PubMed, arXiv, bioRxiv, Semantic Scholar, etc.). This skill should be used when conducting systematic literature reviews, meta-analyses, research... |
| `markdown-mermaid-writing` | Clayton Young / Superior Byte Works, LLC (@borealBytes) | Apache-2.0 | no | Comprehensive markdown and Mermaid diagram writing skill. Use when creating any scientific document, report, analysis, or visualization. Establishes text-based diagrams as the default documentation standard with full style guides... |
| `market-research-reports` | casa | MIT | si | Build evidence-traceable market research reports and assumption-driven market sizing or forecast scenarios. Use for market definition, industry and customer evidence, competitive landscapes, TAM/SAM/SOM reconciliation, forecast... |
| `markitdown` | casa | MIT | si | Convert heterogeneous documents and selected URIs to Markdown with Microsoft MarkItDown for text analysis, search, and LLM/RAG ingestion. Covers safe local conversion, streams, Office/PDF/data formats, batch workflows, plugins, vision... |
| `matchms` | casa | Apache-2.0 | si | Process, clean, compare, and search tandem mass spectra with matchms. Use for MS/MS file I/O, metadata harmonization, peak filtering, spectral similarity, library matching, score matrices, and molecular-similarity networks. Use pyopenms... |
| `matlab` | casa | MIT | si | Build, review, migrate, and safely plan MATLAB or GNU Octave numerical workflows, including arrays, tabular/time data, tests, projects, graphics, MAT files, and explicit Python interoperability. |
| `matplotlib` | casa | https://github.com/matplotlib/matplotlib/tree/main/LICENSE | si | Low-level plotting library for full customization. Use when you need fine-grained control over every plot element, creating novel plot types, or integrating with specific scientific workflows. Export to PNG/PDF/SVG for publication. For... |
| `medchem` | casa | Apache-2.0 | si | Medicinal chemistry filters for compound triage. Apply drug-likeness rules (Lipinski, Veber, CNS), structural alert catalogs (PAINS, NIBR, ChEMBL), complexity metrics, and the medchem query language for library filtering. |
| `modal` | casa | Apache-2.0 | no | Modal is a serverless cloud platform for running Python on demand, including on-demand GPUs. Use when deploying or serving AI/ML models, running GPU-accelerated workloads (training, fine-tuning, inference), serving web endpoints,... |
| `molecular-dynamics` | Kuan-lin Huang | MIT | no | Run and analyze molecular dynamics simulations with OpenMM and MDAnalysis. Set up protein/small molecule systems, define force fields, run energy minimization and production MD, analyze trajectories (RMSD, RMSF, contact maps, free... |
| `molfeat` | casa | Apache-2.0 | no | Molecular featurization for ML (100+ featurizers). ECFP, MACCS, descriptors, pretrained models (ChemBERTa), convert SMILES to features, for QSAR and molecular ML. |
| `ncats-arax` | neuroepithelial | MIT | si | Queries the NCATS Translator ARAX production API for bounded, typed, provenance-rich one-hop and endpoint-pinned two-hop biomedical knowledge-graph relationships. Use for Biolink-constrained RTX-KG2 lookup, explicit selected-provider... |
| `networkx` | casa | 3-clause BSD | no | Create, analyze, and visualize complex networks and graphs in Python with NetworkX. Use when working with network/graph data structures, computing graph algorithms (shortest paths, centrality, clustering), detecting communities,... |
| `neurokit2` | casa | MIT | si | Use NeuroKit2 to build or audit reproducible research workflows for physiological time-series preprocessing, event/interval analysis, multimodal alignment, variability, and complexity. Trigger when code imports neurokit2 or needs its... |
| `neuropixels-analysis` | casa | MIT | si | Analyze Neuropixels extracellular recordings end-to-end with SpikeInterface. Covers loading SpikeGLX/Open Ephys/NWB data, preprocessing, drift/motion correction, Kilosort4 (and CPU) spike sorting, quality metrics, and unit curation... |
| `nextflow` | casa | Apache-2.0 | no | Build, run, and debug Nextflow data pipelines and nf-core workflows end to end. Use whenever the user mentions Nextflow, nf-core, .nf files, nextflow.config, DSL2, processes/channels/operators, samplesheets, or wants to run a community... |
| `omero-integration` | casa | MIT | si | Securely inspect and automate microscopy data workflows against OMERO.server with omero-py, BlitzGateway, OMERO CLI, tables, annotations, ROIs, rendering, and documented OMERO.web APIs. Use for scoped OMERO inventory, metadata export,... |
| `onekgpd` | Dnaerys | MIT | si | > |
| `ontology-term-resolution` | casa | MIT | si | Resolve free-text scientific labels to ontology term IDs and validate existing CURIEs against the EBI Ontology Lookup Service (OLS4). Also look up prefixes in Bioregistry, resolve compact identifiers via Identifiers.org, map lab... |
| `open-notebook` | casa | MIT | si | Self-hosted, open-source alternative to Google NotebookLM for AI-powered research and document analysis. Use when organizing research materials into notebooks, ingesting diverse content sources (PDFs, videos, audio, web pages, Office... |
| `openpiv` | OpenPIV Team | BSD-3-Clause | si | Particle Image Velocimetry (PIV) analysis with OpenPIV. Use when extracting velocity fields from PIV image pairs, analyzing fluid dynamics or flow visualization experiments, cross-correlating interrogation windows, validating and... |
| `opentrons-integration` | casa | MIT | si | Author, review, migrate, simulate, and troubleshoot official Opentrons Python Protocol API v2 protocols for Flex and OT-2 robots. Use for robot-specific liquid handling, deck and labware setup, pipettes, modules, runtime parameters,... |
| `optimize-for-gpu` | casa | MIT | no | GPU-accelerates scientific Python on NVIDIA hardware and verifies that the result is correct and faster. Use for CUDA/GPU optimization; CPU-bound NumPy, SciPy, pandas, scikit-learn, NetworkX, scikit-image, vector-search,... |
| `pacsomatic` | Beifang Niu | MIT | si | Operator toolkit for nf-core/pacsomatic matched tumor-normal workflows from BAM inputs. Use this skill when the user needs to validate run inputs, generate pacsomatic-compliant samplesheets, prepare reproducible Nextflow launch... |
| `paper-lookup` | casa | MIT | si | Search 18 scholarly APIs for papers, preprints, citations, open-access full text, repository records, and journal OA status, and return results with reproducible provenance. Covers PubMed, PMC, Europe PMC, bioRxiv, medRxiv, arXiv,... |
| `paperclip` | casa | MIT | no | Search and read full-text biomedical papers, FDA/PMDA/EMA regulatory documents, clinical trial registries, and UniProt/PDB/ChEMBL entries with the Paperclip CLI from GXL. Covers installing and authenticating the `paperclip` binary with... |
| `paperzilla` | Paperzilla Inc | MIT | no | Chat with your agent about projects, recommendations, and canonical papers in Paperzilla. Use when users ask for recent project recommendations, canonical paper details, markdown-based summaries, recommendation feedback, feed export, or... |
| `parallel-web` | casa | MIT | no | Use Parallel CLI for web search, URL extraction, deep research, structured data enrichment, entity discovery, and recurring web monitoring. Best for requests that explicitly need current web evidence, academic-source discovery, repeated... |
| `pathml` | casa | MIT | si | Use PathML for local, research-only computational pathology workflows: load and tile slides, build preprocessing and QC pipelines, manage h5path data, quantify multiplex images, construct spatial graphs, and plan bounded model inference. |
| `pathogen-variant-surveillance` | casa | MIT | si | Query live pathogen genomic surveillance data through the GenSpectrum LAPIS API to find which viral lineages are circulating now, how fast they are growing, and what mutations they carry. Use whenever a question depends on the current... |
| `pathway-enrichment` | casa | MIT | si | Run pathway and gene-set enrichment analysis on gene lists or ranked gene data, then interpret the results. Use whenever the user has a set of genes (differentially expressed genes from PyDESeq2/Scanpy, CRISPR-screen hits, cluster... |
| `pdf` | Anthropic, PBC | Proprietaria | si | Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks,... |
| `peer-review` | casa | MIT | si | Prepare evidence-bounded, constructive peer-review drafts and structured manuscript assessments. Use for authorized review of scientific manuscripts, protocols, preprints, or research proposals; reporting-guideline selection;... |
| `pennylane` | casa | Apache-2.0 | no | Hardware-agnostic quantum ML framework with automatic differentiation. Use when training quantum circuits via gradients, building hybrid quantum-classical models, or needing device portability across IBM/Google/Rigetti/IonQ. Best for... |
| `phylogenetics` | Kuan-lin Huang | Unknown | si | Build and analyze phylogenetic trees using MAFFT (multiple alignment), IQ-TREE 2 (maximum likelihood), and FastTree (fast NJ/ML). Visualize with ETE3 or FigTree. For evolutionary analysis, microbial genomics, viral phylodynamics,... |
| `pi-agent` | casa | MIT | no | Build with and use Pi, the minimal terminal coding harness. Use for installing Pi, configuring providers/models/settings/environment variables, creating Pi skills/extensions/packages/themes/prompt templates, embedding Pi through the... |
| `pkpd-modeling` | casa | MIT | si | Pharmacokinetic and pharmacodynamic modelling and simulation - non-compartmental analysis, compartmental and population PK, PK/PD and exposure-response, TMDD, PBPK orientation, bioequivalence, allometric scaling and first-in-human dose,... |
| `polars` | casa | https://github.com/pola-rs/polars/blob/main/LICENSE | no | High-performance DataFrame library for Python ETL, analytics, and pandas migration. Use for expression-based data manipulation with lazy query optimization, parallel execution, streaming out-of-core processing, Arrow interoperability,... |
| `polars-bio` | casa | Apache-2.0 | no | High-performance genomic interval operations and bioinformatics file I/O on Polars DataFrames. Overlap, nearest, merge, coverage, complement, subtract for BED/VCF/BAM/GFF intervals. Streaming, cloud-native, faster bioframe alternative. |
| `pptx` | Anthropic, PBC | Proprietaria | si | Use this skill any time a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx or .potx file... |
| `pptx-posters` | casa | MIT | si | Create and audit editable scientific posters in macro-free PowerPoint (.pptx) from author-approved local content and assets. Use when the requested deliverable is a PowerPoint research/conference poster and exact physical, printer,... |
| `primekg` | casa | Unknown | si | Query the Precision Medicine Knowledge Graph (PrimeKG) for multiscale biological data including genes, drugs, diseases, phenotypes, and more. |
| `protocolsio-integration` | casa | MIT | si | Read, validate, and safely export protocols.io data with current official REST/MCP contracts, or create non-executing mutation plans. The bundled client makes bounded official-host GET requests only with explicit --execute. Use only for... |
| `pufferlib` | casa | MIT | si | Version-aware guidance for PufferLib reinforcement-learning environments, vectorization, policies, PuffeRL training, evaluation, and safe checkpoint review. Use when adapting Gymnasium/PettingZoo environments to published PufferLib... |
| `pydeseq2` | casa | MIT | si | Differential gene expression analysis for bulk RNA-seq with PyDESeq2, including formulaic designs, Wald tests, FDR correction, LFC shrinkage, and result visualization. |
| `pydicom` | casa | MIT | si | Use pydicom to read, inspect, write, transform, and safely preflight local DICOM datasets and pixel data. Applies to DICOM metadata, transfer syntaxes, compression plugins, frames, private elements, JSON, and bounded de-identification... |
| `pyhealth` | casa | (non dichiarata) | no | Build clinical/healthcare deep-learning pipelines with PyHealth — loading EHR/signal/imaging datasets (MIMIC-III/IV, eICU, OMOP, SleepEDF, ChestXray14, EHRShot), defining tasks (mortality, readmission, length-of-stay, drug... |
| `pylabrobot` | casa | MIT | si | Develop and review PyLabRobot lab-automation resources, liquid-handling plans, offline simulations, and supported-device integrations. Use for PyLabRobot protocols or API questions; keep physical execution behind an explicit operator... |
| `pymatgen` | casa | MIT | si | Analyze, validate, convert, and transform materials structures and computed materials data with current pymatgen APIs, including local phase diagrams, symmetry sensitivity, electronic-structure I/O, and explicitly bounded Materials... |
| `pymc` | casa | Apache License, Version 2.0 | si | Bayesian modeling with PyMC. Build hierarchical models, MCMC (NUTS), variational inference, LOO/WAIC comparison, posterior checks, for probabilistic programming and inference. |
| `pymoo` | casa | Apache-2.0 | si | Multi-objective optimization framework. NSGA-II, NSGA-III, MOEA/D, Pareto fronts, constraint handling, benchmarks (ZDT, DTLZ), for engineering design and optimization problems. |
| `pyopenms` | casa | 3 clause BSD | si | Complete mass spectrometry analysis platform. Use for proteomics and metabolomics workflows—feature detection, peptide/protein identification, label-free and isobaric quantification, adduct/accurate-mass annotation, and complex LC-MS/MS... |
| `pysam` | casa | MIT | si | Python/HTSlib workflows for genomic files. Use when reading, querying, filtering, or writing SAM/BAM/CRAM, VCF/BCF, FASTA/FASTQ, or tabix data with pysam, including pileup, coverage, indexing, and CRAM references. |
| `pytdc` | casa | MIT | si | Use Therapeutics Data Commons through the PyTDC Python package for registry discovery, approved dataset access, task-aware splits, evaluator metrics, benchmark groups, and bounded molecular-oracle workflows. |
| `pytorch-lightning` | casa | Apache-2.0 | si | Deep learning framework (PyTorch Lightning / lightning package). Organize PyTorch code into LightningModules, configure Trainers for multi-GPU/TPU, implement data pipelines, callbacks, logging (W&B, TensorBoard, MLflow), distributed... |
| `pyzotero` | casa | MIT | no | Interact with Zotero reference management libraries using the pyzotero Python client. Retrieve, create, update, and delete items, collections, tags, and attachments via the Zotero Web API v3. Use this skill when working with Zotero... |
| `qiskit` | casa | Apache-2.0 | si | Build, simulate, transpile, and execute quantum circuits with Qiskit and IBM Quantum Runtime. Use for Qiskit 2.x circuits and operators, V2 Sampler or Estimator primitives, target-aware transpilation, local or noisy simulation, IBM QPU... |
| `qutip` | casa | MIT | si | Simulate and audit closed and open quantum-system models with QuTiP 5, including deterministic, trajectory, steady-state, spectral, and phase-space workflows. Use for local quantum-dynamics work where physical assumptions, dimensions,... |
| `rdkit` | casa | BSD-3-Clause | si | Cheminformatics toolkit for fine-grained molecular control. SMILES/SDF parsing, descriptors (MW, LogP, TPSA), fingerprints, substructure search, 2D/3D generation, similarity, reactions. For standard workflows with simpler interface, use... |
| `relsa-severity-assessment` | casa | MIT | si | Multivariate severity assessment and humane endpoint prediction for laboratory animal studies using the RELSA (RELative Severity Assessment) score and ARIMA-based foRcast forecasting. Use when combining welfare readouts — body weight or... |
| `research-grants` | casa | MIT | no | Write competitive research proposals for NSF, NIH, DOE, DARPA, and Taiwan NSTC. Agency-specific formatting, review criteria, budget preparation, broader impacts, significance statements, innovation narratives, and compliance with... |
| `research-lookup` | casa | MIT | si | Compile current scholarly evidence for a scientific manuscript or research brief. Use when the user explicitly asks to gather literature, references, background evidence, competing findings, or a manuscript research packet. Uses... |
| `rowan` | Rowan Science | Proprietaria | no | Rowan is a cloud-native molecular modeling and medicinal-chemistry workflow platform with a Python API. Use for pKa and macropKa prediction, conformer and tautomer ensembles, docking and analogue docking, protein-ligand cofolding, MSA... |
| `scanpy` | casa | BSD-3-Clause | si | Standard single-cell RNA-seq analysis pipeline. Use for QC, normalization, dimensionality reduction (PCA/UMAP/t-SNE), clustering, differential expression, visualization, and converting R-friendly single-cell formats such as Seurat or... |
| `scholar-evaluation` | casa | MIT | si | Provide qualitative-first, evidence-traceable developmental review of scholarly works and audit low-stakes research-assessment rubrics with optional local quality controls. Never use for ranking people or consequential decisions. |
| `scientific-brainstorming` | casa | MIT | si | Facilitates evidence-aware scientific ideation with independent generation, structured discussion, explicit assumptions, transparent evaluation, adversarial review, and decision logs. Use for early-stage research brainstorming or... |
| `scientific-critical-thinking` | casa | MIT | no | Evaluate scientific claims and evidence quality. Use for assessing experimental design validity, identifying biases and confounders, applying evidence grading frameworks (GRADE, Cochrane Risk of Bias), or teaching critical analysis.... |
| `scientific-schematics` | casa | MIT | si | Create publication-quality scientific diagrams using Nano Banana 2 AI with smart iterative refinement. Uses Gemini 3.6 Flash for quality review. Only regenerates if quality is below threshold for your document type. Specialized in... |
| `scientific-slides` | casa | MIT | si | Build slide decks and presentations for research talks. Use this for making PowerPoint slides, conference presentations, seminar talks, research presentations, thesis defense slides, or any scientific talk. Provides slide structure,... |
| `scientific-visualization` | casa | MIT | si | Create and audit truthful, accessible, publication-ready scientific figures with Matplotlib, Seaborn, or Plotly. Use for figure design, multi-panel layouts, uncertainty and missing-data displays, color/contrast review, image metadata... |
| `scientific-writing` | casa | MIT | si | Draft, revise, and audit scientific manuscripts or reports with explicit evidence provenance, reporting-guideline coverage, authorship accountability, confidentiality controls, and local consistency checks. Use for manuscript sections,... |
| `scikit-bio` | casa | BSD-3-Clause | no | Biological data toolkit. Sequence analysis, alignments, phylogenetic trees, diversity metrics (alpha/beta, UniFrac), ordination (PCoA), PERMANOVA, FASTA/Newick I/O, for microbiome analysis. |
| `scikit-learn` | casa | BSD-3-Clause | si | Machine learning in Python with scikit-learn. Use when working with supervised learning (classification, regression), unsupervised learning (clustering, dimensionality reduction), model evaluation, hyperparameter tuning, preprocessing,... |
| `scikit-survival` | casa | MIT | si | Build, evaluate, and audit right-censored or competing-risk survival workflows with scikit-survival, including leakage-safe preprocessing, model selection, probability prediction, and censoring-aware metrics. |
| `scvelo` | Kuan-lin Huang | BSD-3-Clause | si | RNA velocity analysis with scVelo. Estimate cell state transitions from unspliced/spliced mRNA dynamics, infer trajectory directions, compute latent time, and identify driver genes in single-cell RNA-seq data. Complements... |
| `scvi-tools` | casa | BSD-3-Clause | no | Deep generative models for single-cell omics. Use when you need probabilistic batch correction (scVI), transfer learning, differential expression with uncertainty, or multi-modal integration (TOTALVI, MultiVI). Best for advanced... |
| `seaborn` | casa | BSD-3-Clause | no | Statistical visualization with pandas integration. Use for quick exploration of distributions, relationships, and categorical comparisons with attractive defaults. Best for box plots, violin plots, pair plots, heatmaps. Built on... |
| `shap` | casa | MIT | si | Explain and audit machine-learning predictions with SHAP. Use for selecting SHAP explainers and maskers, computing and validating feature attributions, handling multi-output explanations, and producing local or global SHAP visualizations. |
| `simpy` | casa | MIT | si | Build, inspect, test, and analyze bounded process-based discrete-event simulations with SimPy, including events, resources, interrupts, monitoring, replications, warm-up, and reproducible output analysis. |
| `stable-baselines3` | casa | MIT | si | Production-ready reinforcement learning algorithms (PPO, SAC, DQN, TD3, DDPG, A2C) with scikit-learn-like API. Use for standard RL experiments, quick prototyping, and well-documented algorithm implementations. Best for single-agent RL... |
| `statistical-analysis` | casa | MIT | si | Guided statistical analysis for research data - test selection, assumption checking, effect sizes, power analysis, Bayesian alternatives, and APA-formatted reporting. Use whenever a user wants to compare groups, test a hypothesis,... |
| `statistical-power` | casa | MIT | si | Sample-size and statistical power calculations for planning studies. Use whenever someone asks "how many subjects/samples/replicates do I need", wants an a priori power analysis, a minimum detectable effect (MDE), a power curve, or... |
| `statsmodels` | casa | BSD-3-Clause | no | Statistical models library for Python. Use when you need specific model classes (OLS, GLM, mixed models, ARIMA) with detailed diagnostics, residuals, and inference. Best for econometrics, time series, rigorous inference with coefficient... |
| `sympy` | casa | https://github.com/sympy/sympy/blob/master/LICENSE | no | Use when you need exact symbolic math in Python — algebra, calculus, equation solving, symbolic linear algebra, or code generation via lambdify/LaTeX. Prefer NumPy or SciPy when floating-point approximations are sufficient. |
| `tamarind` | Tamarind Bio | MIT | no | Access a collection of open-source molecular design and structural biology tools on the Tamarind Bio platform, via its REST API or MCP server — no local GPUs required. Tamarind bundles popular open-source models for structure prediction... |
| `tiledbvcf` | Jeremy Leipzig | MIT | no | Efficient storage and retrieval of genomic variant data using TileDB. Scalable VCF/BCF ingestion, incremental sample addition, compressed storage, parallel queries, and export capabilities for population genomics. |
| `timesfm-forecasting` | Clayton Young / Superior Byte Works, LLC (@borealBytes) | Apache-2.0 | si | Zero-shot time series forecasting with Google's TimesFM foundation model. Use for any univariate time series (sales, sensors, energy, vitals, weather) without training a custom model. Supports CSV/DataFrame/array inputs with point... |
| `torch-geometric` | casa | MIT | no | PyTorch Geometric (PyG) for graph neural networks — node/link/graph classification, message passing (GCN, GAT, GraphSAGE, GIN), heterogeneous graphs, neighbor sampling, and custom datasets. Use when working with torch_geometric, not for... |
| `torchdrug` | casa | Apache-2.0 | no | Build and troubleshoot TorchDrug 0.2.1 workflows for molecular graphs, property prediction, self-supervised pretraining, molecule generation, retrosynthesis, protein representation learning, and knowledge graph reasoning. Use when code... |
| `transformers` | casa | Apache-2.0 | no | Hugging Face Transformers for loading Hub models, running pipeline inference, text generation, and Trainer fine-tuning on NLP, vision, audio, and multimodal tasks. Use when working with AutoModel, pipelines, tokenizers, or... |
| `treatment-plans` | casa | MIT | si | Format and structurally validate local treatment-plan documentation after clinical decisions have already been supplied and verified by authorized licensed professionals. Use for source traceability, clinician-authored intervention... |
| `umap-learn` | casa | BSD-3-Clause | no | Use UMAP-learn for nonlinear dimensionality reduction, 2D/3D embeddings, clustering preprocessing, supervised or semi-supervised UMAP, DensMAP, AlignedUMAP, and Parametric UMAP workflows. |
| `uncertainty-and-units` | casa | MIT | si | Track physical units and propagate measurement uncertainty in scientific calculations using pint and uncertainties. Use for unit conversion and dimensional checking, GUM uncertainty budgets, Type A and Type B evaluation, coverage... |
| `usfiscaldata` | casa | MIT | no | Query the U.S. Treasury Fiscal Data REST API for federal financial data. No API key required. Use for national debt (Debt to the Penny), Daily Treasury Statements, Monthly Treasury Statements, Treasury securities auctions, interest... |
| `vaex` | casa | MIT | no | Use this skill for processing and analyzing large tabular datasets (billions of rows) that exceed available RAM. Vaex excels at out-of-core DataFrame operations, lazy evaluation, fast aggregations, efficient visualization of big data,... |
| `venue-templates` | casa | MIT | si | Prepare journal manuscripts, conference papers, research posters, and grant documents using venue-specific formatting guidance and bundled LaTeX scaffolds. Use when selecting an official template, checking current page or anonymity... |
| `waypoint-bio` | casa | MIT | si | Use when working with Outpost Bio's open microbiome foundation models - the Waypoint checkpoints (Waypoint-6m, Waypoint-45m, Waypoint-170m), the Atlas pretraining corpus, the Compass eight-task benchmark, or the `waypoint` CLI from the... |
| `what-if-oracle` | AHK Strategies (ashrafkahoush-ux) | CC BY-NC-SA 4.0 | no | Run structured What-If scenario analysis with 4–6 branch possibility exploration (best, likely, worst, wild card, contrarian, second-order). Use when the user asks speculative what-if questions about uncertain futures, strategic forks,... |
| `xlsx` | Anthropic, PBC | Proprietaria | si | Create, edit, analyze, or convert Excel spreadsheets (.xlsx, .xlsm, .xltx) where the workbook file is the primary deliverable. Use for formulas, formatting, financial models, multi-sheet workbooks, and tabular cleanup exported to Excel.... |
| `zarr-python` | casa | MIT | no | Chunked N-D arrays for cloud storage (Zarr-Python 3). Compressed arrays, parallel I/O, S3/GCS via fsspec, NumPy/Dask/Xarray compatible, for large-scale scientific computing pipelines. |

Copia letta in `C:/Users/Utente/AppData/Local/Temp/claude/E--template-claude-developing/5a044334-d906-4e16-8242-c82bf2fd539f/scratchpad/kd`.
