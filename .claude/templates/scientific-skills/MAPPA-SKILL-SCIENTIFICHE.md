# Mappa delle skill scientifiche

> Documento generato da `tools/mappa-skill-scientifiche.py` leggendo una copia locale di `K-Dense-AI/scientific-agent-skills`. Non si scrive a mano: si rigenera. Le tre colonne che contano sono l'autore, la licenza e la presenza di programmi eseguibili, perché sono i tre criteri che l'avviso di sicurezza della raccolta chiede di guardare prima di installare.

## In breve

Sono 177 skill. Ne ha scritte 151 la casa che mantiene la raccolta e 26 altri autori, e la differenza è dichiarata a monte come differenza di profondità della revisione. Ne portano programmi eseguibili 121, cioè la maggioranza, ed è la classe per cui vale passare uno scanner prima di installare. Ne hanno licenza proprietaria 1, dentro una raccolta che si presenta come MIT. E 23 coprono un terreno che un pacchetto di questo sistema già copre.

| Licenza | Skill |
|---|---|
| MIT | 117 |
| Apache-2.0 | 19 |
| BSD-3-Clause | 16 |
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
| Proprietaria | 1 |
| https://github.com/sympy/sympy/blob/master/LICENSE | 1 |
| CC BY-NC-SA 4.0 | 1 |

Gli autori diversi dalla casa, con quante skill ciascuno: Kuan-lin Huang (5), AHK Strategies (ashrafkahoush-ux) (3), Clayton Young / Superior Byte Works, LLC (@borealBytes) (2), BGPT (1), Yaroslav Halchenko (1), Dylan Pulver (1), Ratschlab, ETH Zurich (1), Exa (1), Helena Bioinformatics (1), Genomic Intelligence (1), Andrey Fedorov, @fedorov (1), neuroepithelial (1), Dnaerys (1), OpenPIV Team (1), Beifang Niu (1), Paperzilla Inc (1), Rowan Science (1), Tamarind Bio (1), Jeremy Leipzig (1).

## I settori, come li dichiara la raccolta

Sono la tassonomia di chi la mantiene, letta dal suo README e non inventata qui. Servono al gate dei pacchetti per capire quale porzione della raccolta riguardi un progetto: quasi sempre è una sola riga di questa tabella.

| Settore | Skill dichiarate |
|---|---|
| Bioinformatics & Genomics | 32 |
| Cheminformatics & Drug Discovery | 11 |
| Proteomics & Mass Spectrometry | 2 |
| Clinical Research & Evidence Workflows | 8 |
| Preclinical Research & Animal Welfare | 1 |
| Microscopy, Medical Imaging & Digital Pathology | 5 |
| Neuroscience & Electrophysiology | 4 |
| Materials Science, Chemistry & Physics | 8 |
| Engineering & Simulation | 9 |
| Chemical Oceanography | 1 |
| Data Analysis & Visualization | 18 |
| Laboratory Automation | 6 |
| Multi-omics & Systems Biology | 5 |
| Protein Engineering & Design | 5 |
| Scientific Communication | 23 |
| Infrastructure & Platforms | 12 |
| Research Methodology & Planning | 13 |
| Regulatory & Standards | 2 |

Le categorie dichiarano 165 skill in totale contro le 177 presenti sul disco. Lo scarto non è un errore di questo programma: le categorie del README si sovrappongono e alcune skill vi compaiono due volte o nessuna. Va letto come indicazione della grandezza di un settore, non come conteggio.

## Le skill che questo sistema copre già

Righe da non prendere senza avere deciso quale delle due capacità resta in uso, e da registrare come decisione quando si prende comunque quella di là.

| Skill | Che cosa in questo sistema copre già lo stesso terreno |
|---|---|
| `bgpt-paper-search` | academic-researcher, semantic-scholar-mcp |
| `citation-management` | book-bib-extract, zotero-mcp, refchecker-mcp |
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
| `peer-review` | academic-researcher |
| `pyzotero` | zotero-mcp |
| `research-lookup` | academic-researcher, academix |
| `scholar-evaluation` | academic-researcher |
| `scientific-schematics` | diagrams |
| `scientific-visualization` | la skill nativa dataviz |
| `scientific-writing` | interaction-style.md, humanizer |
| `seaborn` | la skill nativa dataviz |
| `venue-templates` | latex |

## Tutte le skill

La colonna del codice dice se la skill porta una cartella `scripts/` con programmi eseguibili. La colonna dell'autore dice soltanto se sia della casa: e lo fa secondo il criterio che la raccolta stessa indica per sapere quanta revisione quella skill abbia avuto.

| Skill | Autore | Licenza | Codice | Che cosa fa |
|---|---|---|---|---|
| `13c-metabolic-flux` | casa | MIT | si | Estimates intracellular metabolic fluxes from steady-state carbon-13 isotope-tracing measurements using validated atom maps, mfapy isotope simulation, constrained multistart fitting, and flux-profile diagnostics. Use for 13C-MFA, carbon... |
| `adaptyv` | casa | MIT | no | Uses the Adaptyv Bio Foundry API and Python SDK to design protein characterization experiments, estimate costs, submit sequences, monitor laboratory progress, and retrieve results. Applies to Adaptyv Foundry, its target catalog, binding... |
| `aeon` | casa | BSD-3-Clause | no | This skill should be used for time series machine learning tasks including classification, regression, clustering, forecasting, anomaly detection, segmentation, and similarity search. Use when working with temporal data, sequential... |
| `alphagenome` | casa | MIT | si | Looks up precomputed AlphaGenome Atlas effects for any GRCh38 single-nucleotide variant (AVI score with Phred and 18 SHAP feature attributions, plus raw and quantile scores for RNA-seq, DNase, ATAC, ChIP-TF, ChIP-histone, CAGE, PRO-cap,... |
| `analytical-method-validation` | casa | MIT | si | Plans, executes, and documents validation, verification, and transfer of analytical procedures under the governing framework - ICH Q2(R2) and Q14, USP <1220>/<1225>/<1226>, ICH M10 bioanalytical, CLSI EP, or ISO/IEC 17025. Use for HPLC,... |
| `anndata` | casa | BSD-3-Clause | no | Handles annotated matrices in single-cell analysis, .h5ad and Zarr files, and integration with the scverse ecosystem. This is the data format skill—for analysis workflows use scanpy; for probabilistic models use scvi-tools; for... |
| `arbor` | casa | MIT | si | Applies Arbor Hypothesis Tree Refinement to research artifacts with repeatable evaluators, including model training, agent harnesses, data synthesis and benchmark optimization. Uses persistent hypotheses, isolated experiments, evidence... |
| `arboreto` | casa | BSD-3-Clause | si | Infers candidate gene regulatory networks from bulk or single-cell expression data using AertsLab Arboreto GRNBoost2 and GENIE3. Use for transcription factor-target association ranking, compatible Dask execution, sparse expression... |
| `astropy` | casa | BSD-3-Clause | no | Core Python library for astronomy and astrophysics workflows that need Astropy APIs, including units/quantities, coordinates, FITS I/O, tables, time systems, WCS, and cosmology. Use when implementing or debugging astronomical data... |
| `autoskill` | casa | MIT | si | Analyzes user-requested Screenpipe history windows to detect repeated research workflows, match existing scientific skills, and stage new skill drafts or composition recipes for review. Requires a reachable Screenpipe HTTP API, normally... |
| `benchling-integration` | casa | MIT | no | Benchling Python SDK and REST API integration for registry entities, inventory, ELN entries, workflows, Benchling Apps, and Data Warehouse queries. Use when automating lab data with benchling-sdk or the v2 API. |
| `bgpt-paper-search` | BGPT | MIT | no | Searches BGPT scientific papers by topic or DOI and retrieves claim-level evidence extracted from full text, including experiments, reported statistics, scope, limitations, and provenance. Use for literature reviews, evidence synthesis,... |
| `bids` | Yaroslav Halchenko | https://creativecommons.org/licenses/by/4.0/ | si | > |
| `biopython` | casa | Biopython License Agreement | no | Provides Biopython workflows for sequence manipulation, file parsing (FASTA/GenBank/PDB), phylogenetics, and programmatic NCBI/PubMed access (Bio.Entrez). Supports batch processing, custom molecular-biology pipelines, BLAST automation,... |
| `bioservices` | casa | GPLv3 | si | Provides a Python interface to bioinformatics services including UniProt, KEGG, ChEMBL, Reactome, QuickGO, and UniChem. Used for cross-database protein annotation, pathway retrieval, chemical identifier mapping, and integrated... |
| `bulk-rnaseq` | casa | MIT | si | Prepares bulk RNA-seq FASTQ, Salmon, STAR or featureCounts output for gene-level differential expression. Covers nf-core/rnaseq and standalone quantification, biological replication, strandedness, reference provenance, validated count... |
| `cantera` | casa | MIT | si | Runs Cantera homogeneous chemical reactors and evaluates ignition delay with mechanism provenance, conservation checks, and numerical refinement. Use for combustion kinetics, closed adiabatic ideal-gas constant-volume or... |
| `cellprofiler` | casa | MIT | si | Runs reproducible CellProfiler microscopy pipelines for nuclear segmentation, cell counts, and per-object fluorescence measurements. Supports image/channel manifests, headless batch execution, segmentation overlays, and measurement QC... |
| `cellxgene-census` | casa | MIT | no | Queries the CZ CELLxGENE Census programmatically for versioned public single-cell and spatial transcriptomics data. Use when you need population-scale cell metadata, gene expression slices, Census summary counts, source H5AD... |
| `cirq` | casa | Apache-2.0 | no | Google quantum computing framework. Use when targeting Google Quantum AI hardware, designing noise-aware circuits, or running quantum characterization experiments. Best for Google hardware, noise modeling, and low-level circuit design.... |
| `citation-management` | casa | MIT | si | Comprehensive citation management for academic research. Search OpenAlex, PubMed, and Google Scholar for papers, extract accurate metadata, validate citations, and generate properly formatted BibTeX entries. This skill should be used... |
| `clinical-decision-support` | casa | MIT | si | Prepares and validates research-only clinical decision-support evaluation, evidence-profile, cohort, survival, biomarker/model, privacy, and governance artifacts. Supports aggregate or synthetic research documentation and traceability,... |
| `clinical-reports` | casa | MIT | si | Creates safety-bounded draft structures and runs local deterministic checks for clinical case, diagnostic, trial, safety, and aggregate research reports. Use only with synthetic, de-identified, or aggregate inputs and verified... |
| `cobrapy` | casa | GPL-2.0 | no | Performs constraint-based metabolic modeling with COBRApy, including FBA, pFBA, FVA, gene knockouts, flux sampling, growth media, production envelopes, gap filling, and SBML model validation for systems biology and metabolic engineering. |
| `consciousness-council` | AHK Strategies (ashrafkahoush-ux) | MIT | no | Structures a multi-perspective council exercise for decisions, research trade-offs, and creative challenges. Simulates thinking archetypes, separates evidence from assumptions and values, and synthesizes a conditional recommendation.... |
| `dask` | casa | BSD-3-Clause | no | Scales pandas, NumPy, and custom Python research workflows beyond memory or across clusters with Dask. Covers DataFrames, Arrays, Bags, Futures, chunking, schedulers, and distributed diagnostics. Use for partitioned file processing,... |
| `database-lookup` | casa | MIT | no | Queries documented public database APIs with explicit endpoints, filters, pagination, and provenance. Used when a scientific, regulatory, financial, or other database-backed fact must be retrieved reproducibly from a named source rather... |
| `datalad` | Dylan Pulver | MIT | no | Retrieves, versions, and publishes scientific datasets with DataLad and git-annex, and captures computational provenance with datalad run, rerun, and containers-run. Use when cloning or fetching data from OpenNeuro, DANDI,... |
| `datamol` | casa | Apache-2.0 | no | Pythonic wrapper around RDKit with simplified interface and sensible defaults. Preferred for standard drug discovery including SMILES parsing, standardization, descriptors, fingerprints, clustering, 3D conformers, parallel processing.... |
| `deepchem` | casa | MIT | si | Builds molecular property prediction and MoleculeNet workflows with DeepChem, including SMILES featurization, scaffold or grouped holdouts, masked labels, graph models and explicit pretrained encoder transfer. Used for ADMET, toxicity,... |
| `deepspot-m` | Ratschlab, ETH Zurich | PolyForm-Noncommercial-1.0.0 | no | Generates transcriptome-wide virtual spatial transcriptomics from H&E histology with DeepSpot-M. Used for predicted log1p-CPM expression from 224x224 tiles at about 20x, querying the released protein-coding gene panel by symbol, and... |
| `deeptools` | casa | BSD | si | NGS analysis toolkit. BAM to bigWig conversion, QC (correlation, PCA, fingerprints), heatmaps/profiles (TSS, peaks), for ChIP-seq, RNA-seq, ATAC-seq visualization. |
| `depmap` | Kuan-lin Huang | CC-BY-4.0 | si | Retrieves and analyzes Cancer Dependency Map (DepMap) release data, including CRISPR Chronos gene effects, cancer model annotations, omics biomarkers, and PRISM drug sensitivity. Supports cancer-selective dependency, co-essentiality,... |
| `dhdna-profiler` | AHK Strategies (ashrafkahoush-ux) | MIT | no | Applies the DHDNA framework as an exploratory rubric for reasoning and writing patterns in supplied text. Used for explicit requests for DHDNA, cognitive-style reflection, a thinking-pattern profile, or comparisons of textual reasoning.... |
| `diffdock` | casa | MIT | si | Predicts protein-small-molecule binding poses with DiffDock and DiffDock-L from PDB or sequence plus SMILES/SDF/MOL2. Covers batch docking, pose triage, confidence interpretation, and validation. Use for molecular docking and... |
| `dnanexus-integration` | casa | MIT | si | Builds and operates reproducible genomics workloads on DNAnexus with the dx CLI, dxpy, apps/applets, native workflows, dxCompiler, and Nextflow. Supports DNAnexus data transfers, dxapp.json development, execution monitoring, workflow... |
| `esm` | casa | MIT | si | Uses the Biohub esm Python SDK for ESM3 protein generation, ESMC embeddings, and ESMFold2 all-atom folding. Applies to local model inference and Biohub hosted clients, including former Forge workflows; distinguishes the separate legacy... |
| `etetoolkit` | casa | GPL-3.0-or-later | si | Analyzes, manipulates, compares, annotates, and visualizes phylogenetic or other hierarchical trees with ETE 4. Supports Newick/Nexus tree I/O, topology edits and pattern matching, Robinson-Foulds comparisons, gene-tree evolutionary... |
| `exa-search` | Exa | MIT | si | Searches scientific and technical web content with Exa and extracts page or PDF text from URLs in batches. Supports scholarly discovery with the publication category and academic domain filters. Applies to requests to search the web,... |
| `experimental-design` | casa | MIT | si | Designs experiments and studies BEFORE data is collected — choosing a design, randomizing, blocking, and laying out treatment combinations so results are interpretable. Use whenever someone is planning a study, asks how to assign... |
| `exploratory-data-analysis` | casa | MIT | si | Performs bounded, local exploratory analysis of explicitly supported scientific files. Supports redacted CSV/TSV/JSON profiles; optional NumPy, HDF5, FASTA/FASTQ, and basic image metadata inspection; missingness/leakage audits; outlier... |
| `fictiv` | casa | MIT | si | Operates Fictiv (app.fictiv.com), the on-demand manufacturing platform, end to end in the user's browser. Covers uploading CAD parts, configuring process, material, finish, threads, tolerances and inspections, getting instant or manual... |
| `flowio` | casa | BSD-3-Clause | si | Reads, inspects, and writes Flow Cytometry Standard (FCS) 2.0, 3.0, and 3.1 files with FlowIO. Use for low-level FCS metadata and channel inspection, NumPy event extraction, multi-dataset files, table export, and FCS 3.1 creation; use... |
| `flowkit` | casa | MIT | si | Analyzes flow cytometry data with FlowKit, including spillover compensation, logicle and biexponential transforms, hierarchical gating, GatingML strategies, and supported FlowJo 10 workspaces. Use for reproducible gate counts,... |
| `fluidsim` | casa | MIT | si | Plans, configures, inspects, restarts, and analyzes bounded FluidSim computational-fluid-dynamics simulations with explicit numerical-validity and HPC safety checks. Use for FluidSim solver selection, parameter review, FFT/MPI setup,... |
| `folklore-variant-evidence` | Helena Bioinformatics | MIT | no | Retrieves ClinGen gene-disease validity assertions for a public gene or disease, and reviews source-linked public evidence and literature for one supported GRCh38 germline nuclear SNV or simple indel through Folklore Clinical Variant... |
| `generate-image` | casa | MIT | si | Generates or edits images with AI models through the OpenRouter Image API (Gemini, Seedream, Recraft, GPT-Image, Riverflow). Use for photos, illustrations, artwork, concept art, visual assets, logos, and image editing or compositing... |
| `geniml` | casa | MIT | si | Supports audited local Geniml genomic-interval workflows: validate BED and universe contracts, plan Region2Vec or scEmbed runs, inspect model/tokenizer compatibility, and assess consensus universes. |
| `genomic-coordinates` | casa | MIT | si | Converts genomic intervals between coordinate conventions, normalises and compares variant representations, and detects assembly or contig-naming mismatches before they corrupt an analysis. Used whenever coordinates cross a format,... |
| `genomic-intelligence` | Genomic Intelligence | MIT | no | Predicts regulatory features, gene structure, and expression directly from DNA sequence using Genomic Intelligence's hosted transformer DNA language models — no local GPU or model weights. Six tasks over a REST API and a hosted MCP... |
| `geomaster` | casa | MIT | si | Supports geospatial research workflows for remote sensing, vector and raster GIS, spatial statistics, terrain and network analysis, and machine learning for Earth observation. Use when processing satellite imagery, aligning coordinate... |
| `geopandas` | casa | MIT | si | Guidance and local audit tools for Python workflows that directly use GeoPandas GeoSeries, GeoDataFrame, spatial operations, or vector-data I/O. |
| `get-available-resources` | casa | MIT | si | Detects host inventory and effective CPU, memory, disk, scheduler, container, and accelerator limits when a user asks for resource-aware planning or before a clearly resource-sensitive local workload. Produces a redacted JSON snapshot... |
| `gget` | casa | BSD-2-Clause | si | Queries 20+ bioinformatics resources through CLI/Python. Supports quick lookups of gene info, BLAST/BLAT, viral sequence downloads, PDB/mmCIF structures, G2P residue annotations, enrichment analysis, OpenTargets, COSMIC, CELLxGENE, and... |
| `ginkgo-cloud-lab` | casa | MIT | no | Guides protocol selection, input preparation, pricing checks, and browser ordering on Ginkgo Bioworks Cloud Lab (cloud.ginkgo.bio). Applies to cell-free, E. coli, and Pichia protein expression; HiBiT, A280, and LabChip readouts; IVT... |
| `glycoengineering` | Kuan-lin Huang | Unknown | si | Analyzes and engineers protein glycosylation by scanning canonical N-glycosylation sequons, describing S/T-rich regions, checking curated glycan evidence, and preparing NetNGlyc, NetOGlyc and GlycoSHIELD workflows. Use for glycoprotein... |
| `gtars` | casa | MIT | si | Supports Gtars for local genomic interval models and set algebra, overlaps and counts, consensus and coverage, tokenization, fragment processing, and refget/BEDbase planning across Python, Rust, and the CLI. |
| `histolab` | casa | Apache-2.0 | no | Extracts and preprocesses whole-slide histology image tiles with Histolab. Use for WSI inspection, tissue masks, random/grid/score-based tile extraction, H&E stain normalization, and tile dataset preparation. For multiplexed imaging or... |
| `hugging-science` | casa | (non dichiarata) | si | Discovers and evaluates scientific datasets, models, methodology posts, and Spaces through the Hugging Science catalog. Used when selecting scientific ML resources in biology, chemistry, genomics, materials, climate, physics, astronomy,... |
| `hypogenic` | casa | MIT | si | Plans and audits use of ChicagoHAI HypoGeniC/HypoRefine for LLM-assisted hypothesis generation from labeled text datasets. Use for the `hypogenic` package, its task configs, hypothesis banks, or HypoBench datasets—not for manual... |
| `hypothesis-generation` | casa | MIT | si | Formulates evidence-bounded scientific questions, candidate hypotheses, rival explanations, causal or associational claims, discriminating predictions, measurements, and preregistration-ready analysis plans. Used when turning... |
| `imaging-data-commons` | Andrey Fedorov, @fedorov | This skill is provided under the MIT License. IDC data itself has individual licensing (mostly CC-BY, some CC-NC) that must be respected when using the data. | si | Queries and downloads public cancer imaging data from NCI Imaging Data Commons. Supports IDC collection discovery, DICOM access, radiology (CT, MR, PET) and pathology AI datasets, metadata SQL, visualization, licensing, and citations.... |
| `infographics` | casa | (non dichiarata) | si | Creates and reviews infographics with Nano Banana 2 via OpenRouter. Use for statistical summaries, timelines, comparisons, processes, and visual explanations with supplied data or optional Sonar research. Supports ten layouts, eight... |
| `iso-standards-readiness` | casa | MIT | si | Prepares and structurally reviews readiness evidence for ISO management-system and laboratory-competence standards - ISO 13485 medical device QMS, ISO 14971 device risk management, ISO/IEC 17025 testing and calibration laboratories, and... |
| `lab-hardware-cad` | casa | MIT | si | Designs custom laboratory hardware as parametric build123d models and exports fabrication artifacts as STEP, STL, and DXF files - microfluidic chips and molds, optomechanical mounts and breadboard adapters, cuvette and microplate... |
| `labarchive-integration` | casa | MIT | si | Integrates with the official LabArchives ELN REST-like API and Inventory API v1. Supports regional endpoint selection, signed-request construction, user authorization and UID flows, local LA container validation, and verified... |
| `lamindb` | casa | Apache-2.0 | no | Manages biological datasets and models with LaminDB, including artifact registration, lineage tracking, schema validation, Bionty ontology annotation, query/search, collections, branches, storage, and workflow integrations. Use for... |
| `latchbio-integration` | casa | MIT | si | Builds, registers, debugs, and operates bioinformatics workflows on Latch using the Python SDK, CLI, Latch Data and Registry, Nextflow, Snakemake, programmatic execution, and Latch MCP. Use when authoring or deploying Latch workflows,... |
| `latex-posters` | casa | (non dichiarata) | si | Creates research posters in LaTeX using beamerposter, tikzposter, or baposter. Use for conference posters, academic presentations, multi-column scientific layouts, figure integration, typography, compilation, and PDF preflight. |
| `liteparse` | casa | Apache-2.0 | si | Local document and PDF parsing that returns spatial text with bounding boxes. Use for extracting text from PDFs, DOCX, Office files, and images; running OCR on scans; producing layout-preserved JSON for RAG; batch-ingesting folders of... |
| `literature-review` | casa | MIT | si | Conducts systematic, scoping, and narrative literature reviews using PubMed, arXiv, bioRxiv, Semantic Scholar, and other appropriate sources. Use for research synthesis, reproducible literature searches, screening, citation checking, or... |
| `mageck` | casa | MIT | si | Analyzes pooled CRISPR screen FASTQ reads and guide-count matrices with MAGeCK, validates guide libraries and contrasts, measures replicate and library QC, and produces gene hit rankings with effect sizes and FDR. Use for new knockout,... |
| `marine-carbonate-chemistry` | casa | MIT | si | Solves seawater carbonate chemistry with PyCO2SYS for chemical oceanography, ocean acidification, and marine carbon-cycle research. Use for paired total alkalinity, dissolved inorganic carbon, pH, or seawater pCO2/fCO2 measurements;... |
| `markdown-mermaid-writing` | Clayton Young / Superior Byte Works, LLC (@borealBytes) | Apache-2.0 | no | Writes scientific Markdown documentation and Mermaid diagrams for workflows, relationships, timelines, and schemas. Provides syntax references, document templates, accessibility guidance, and version-aware rendering checks. Use when a... |
| `market-research-reports` | casa | MIT | si | Builds evidence-traceable market research reports and assumption-driven market sizing or forecast scenarios. Use for market definition, industry and customer evidence, competitive landscapes, TAM/SAM/SOM reconciliation, forecast... |
| `markitdown` | casa | MIT | si | Converts heterogeneous documents and selected URIs to Markdown with Microsoft MarkItDown for text analysis, search, and LLM/RAG ingestion. Covers safe local conversion, streams, Office/PDF/data formats, batch workflows, plugins, vision... |
| `matchms` | casa | Apache-2.0 | si | Processes, cleans, compares, and searches tandem mass spectra with matchms. Use for MS/MS file I/O, metadata harmonization, peak filtering, spectral similarity, library matching, score matrices, and molecular-similarity networks. Use... |
| `matlab` | casa | MIT | si | Builds, reviews, migrates, and plans MATLAB or GNU Octave numerical workflows. Use for arrays, tabular/time data, tests, projects, graphics, MAT files, and explicit Python interoperability. |
| `matplotlib` | casa | https://github.com/matplotlib/matplotlib/tree/main/LICENSE | si | Creates and customizes scientific plots with Matplotlib. Used for fine-grained control over plot elements, novel plot types, and scientific workflows. Export to PNG/PDF/SVG for publication. For quick statistical plots use seaborn; for... |
| `medchem` | casa | Apache-2.0 | si | Applies medicinal chemistry filters for compound triage, using drug-likeness rules (Lipinski, Veber, CNS), structural alert catalogs (PAINS, NIBR, ChEMBL), complexity metrics, and the medchem query language for library filtering. |
| `modal` | casa | Apache-2.0 | no | Modal is a serverless cloud platform for running Python on demand, including on-demand GPUs. Use when deploying or serving AI/ML models, running GPU-accelerated workloads (training, fine-tuning, inference), serving web endpoints,... |
| `molecular-dynamics` | Kuan-lin Huang | MIT | no | Runs and analyzes molecular dynamics simulations with OpenMM and MDAnalysis. Sets up protein/small molecule systems, defines force fields, runs energy minimization and production MD, and analyzes trajectories (RMSD, RMSF, contact maps,... |
| `molfeat` | casa | Apache-2.0 | no | Featurizes small molecules with Molfeat for QSAR/QSPR, chemical similarity, virtual screening, and molecular ML. Covers ECFP/MACCS fingerprints, RDKit descriptors, pharmacophores, pretrained embeddings, configuration persistence, and... |
| `ncats-arax` | neuroepithelial | MIT | si | Queries the NCATS Translator ARAX production API for bounded, typed, provenance-rich one-hop and endpoint-pinned two-hop biomedical knowledge-graph relationships. Use for Biolink-constrained RTX-KG2 lookup, explicit selected-provider... |
| `networkx` | casa | 3-clause BSD | no | Creates, analyzes, and visualizes complex networks and graphs in Python with NetworkX. Use when working with network/graph data structures, computing graph algorithms (shortest paths, centrality, clustering), detecting communities,... |
| `neurokit2` | casa | MIT | si | Builds and audits reproducible NeuroKit2 research workflows for physiological time-series preprocessing, event/interval analysis, multimodal alignment, variability, and complexity. Use when code imports neurokit2 or needs its current... |
| `neuropixels-analysis` | casa | MIT | si | Analyzes Neuropixels extracellular recordings end-to-end with SpikeInterface. Covers loading SpikeGLX/Open Ephys/NWB data, preprocessing, drift/motion correction, Kilosort4 (and CPU) spike sorting, quality metrics, and unit curation... |
| `nextflow` | casa | Apache-2.0 | no | Builds, runs, and debugs Nextflow DSL2 pipelines and nf-core workflows. Use for Nextflow, nf-core, .nf files, nextflow.config, processes/channels/operators, samplesheets, nf-test, modules/subworkflows, container and executor... |
| `nmrglue` | casa | MIT | si | Processes calibrated one-dimensional complex NMR free-induction decays with nmrglue into phased spectra, peak candidates, and signed integration regions. Use for raw 1D NMR processing, ppm-axis verification, apodization, Fourier... |
| `nwb-conversion` | casa | MIT | si | Converts neuroscience acquisition data to Neurodata Without Borders files with NeuroConv and PyNWB, preserves metadata and timebases, checks evidence-based clock alignment, and produces schema validation, NWB Inspector findings and... |
| `omero-integration` | casa | MIT | si | Inspects and automates microscopy data workflows against OMERO.server with omero-py, BlitzGateway, OMERO CLI, tables, annotations, ROIs, rendering, and documented OMERO.web APIs. Use this skill for scoped OMERO inventory, metadata... |
| `onekgpd` | Dnaerys | MIT | si | > |
| `ontology-term-resolution` | casa | MIT | si | Resolves free-text scientific labels to ontology term IDs and validates existing CURIEs against the EBI Ontology Lookup Service (OLS4). Also looks up prefixes in Bioregistry, resolves compact identifiers via Identifiers.org, maps lab... |
| `open-notebook` | casa | MIT | si | Organizes research with the self-hosted Open Notebook alternative to NotebookLM. Supports source ingestion (PDFs, web pages, audio, video, and Office documents), cited document chat, text and vector search, notes, custom... |
| `openpiv` | OpenPIV Team | BSD-3-Clause | si | Performs Particle Image Velocimetry (PIV) analysis with OpenPIV. Use when extracting velocity fields from PIV image pairs, analyzing fluid dynamics or flow visualization experiments, cross-correlating interrogation windows, validating... |
| `opentrons-integration` | casa | MIT | si | Authors, reviews, migrates, simulates, and troubleshoots official Opentrons Python Protocol API v2 protocols for Flex and OT-2 robots. Use for robot-specific liquid handling, deck and labware setup, pipettes, modules, runtime... |
| `optimize-for-gpu` | casa | MIT | no | GPU-accelerates scientific Python on NVIDIA hardware and verifies that the result is correct and faster. Use for CUDA/GPU optimization; CPU-bound NumPy, SciPy, pandas, scikit-learn, NetworkX, scikit-image, vector-search,... |
| `pacsomatic` | Beifang Niu | MIT | si | Prepares and launches nf-core/pacsomatic matched tumor-normal PacBio HiFi genomics workflows from unaligned BAM inputs. Supports samplesheet generation, pinned Nextflow launch artifacts, local checks, LSF/Slurm/PBS Pro/SGE launcher... |
| `paper-lookup` | casa | MIT | si | Searches 18 scholarly APIs for papers, preprints, citations, open-access full text, repository records, and journal OA status, and returns results with reproducible provenance. Covers PubMed, PMC, Europe PMC, bioRxiv, medRxiv, arXiv,... |
| `paperclip` | casa | MIT | no | Searches and reads biomedical papers, FDA/PMDA/EMA documents, clinical trials, and protein records with the GXL Paperclip CLI and Python SDK. Supports source-scoped search, full-text grep, metadata SQL, map/reduce extraction, figure... |
| `paperzilla` | Paperzilla Inc | MIT | no | Reads projects, searches project feeds, and retrieves recommendations and canonical papers in Paperzilla through the pz CLI. Supports recent recommendations, paper details, markdown-based summaries, recommendation feedback, JSON export,... |
| `parallel-web` | casa | MIT | no | Uses Parallel CLI for web search, URL extraction, deep research, structured data enrichment, entity discovery, and recurring web monitoring. Best for requests that explicitly need current web evidence, academic-source discovery,... |
| `pathml` | casa | MIT | si | Supports local computational pathology research with PathML: slide loading and tiling, preprocessing and QC, h5path storage, multiplex quantification, spatial graphs, and bounded model inference. Use for whole-slide H&E, CODEX, Vectra,... |
| `pathogen-variant-surveillance` | casa | MIT | si | Queries public GenSpectrum LAPIS data for pathogen genomic surveillance, current lineage nomenclature, weekly sequence proportions, reporting delays, and descriptive mutation frequencies. Use for variant surveillance, Pango lineage... |
| `pathway-enrichment` | casa | MIT | si | Performs pathway and gene-set enrichment analysis on gene lists or ranked gene data and interprets the results. Used when the user has a set of genes (differentially expressed genes from PyDESeq2/Scanpy, CRISPR-screen hits, cluster... |
| `peer-review` | casa | MIT | si | Prepares evidence-bounded, constructive peer-review drafts and structured manuscript assessments. Supports authorized review of scientific manuscripts, protocols, preprints, or research proposals; reporting-guideline selection;... |
| `pennylane` | casa | Apache-2.0 | no | Builds and differentiates PennyLane quantum circuits, hybrid PyTorch or JAX models, molecular VQE and QAOA workflows. Use for variational quantum algorithms, quantum machine learning, simulator validation, and moving validated circuits... |
| `phylogenetics` | Kuan-lin Huang | Unknown | si | Builds and analyzes phylogenetic trees using MAFFT multiple sequence alignment, IQ-TREE maximum likelihood with ModelFinder and branch support, and FastTree approximate inference. Uses ETE3 for tree summaries and visualization. Applies... |
| `pi-agent` | casa | MIT | no | Builds with and operates Pi, the minimal terminal coding harness. Use for installing Pi, configuring providers/models/settings/environment variables, creating Pi skills/extensions/packages/themes/prompt templates, embedding Pi through... |
| `pkpd-modeling` | casa | MIT | si | Pharmacokinetic and pharmacodynamic modelling and simulation - non-compartmental analysis, compartmental and population PK, PK/PD and exposure-response, TMDD, PBPK orientation, bioequivalence, allometric scaling and first-in-human dose,... |
| `polars` | casa | https://github.com/pola-rs/polars/blob/main/LICENSE | no | High-performance DataFrame library for Python ETL, analytics, and pandas migration. It supports expression-based data manipulation with lazy query optimization, parallel execution, streaming out-of-core processing, Arrow... |
| `polars-bio` | casa | Apache-2.0 | no | Performs genomic interval overlap, nearest, merge, coverage, complement and subtraction on Polars DataFrames, and reads or writes BED, VCF, BCF, BAM, CRAM, GFF, GTF, FASTA and FASTQ data. Use for coordinate-aware genomic joins,... |
| `pptx-posters` | casa | MIT | si | Creates and audits editable scientific posters in macro-free PowerPoint (.pptx) from author-approved local content and assets. Used when the requested deliverable is a PowerPoint research/conference poster and exact physical, printer,... |
| `primekg` | casa | Unknown | si | Queries a pinned Precision Medicine Knowledge Graph (PrimeKG) CSV for typed gene, drug, disease, and phenotype nodes, direct associations, disease context, and one- or two-hop paths. Use for PrimeKG reproducibility, biological... |
| `primer-design` | casa | MIT | si | Designs and audits PCR and RT-qPCR primers with Primer3, explicit thermodynamic conditions, reference-based off-target amplification searches, and traceable sequence coordinates. Use for designing primer pairs, checking existing... |
| `protocolsio-integration` | casa | MIT | si | Reads, validates, and safely exports protocols.io data with current official REST/MCP contracts, or creates non-executing mutation plans. The bundled client makes bounded official-host GET requests only with explicit --execute. Use only... |
| `pufferlib` | casa | MIT | si | Version-aware guidance for PufferLib reinforcement-learning environments, vectorization, policies, PuffeRL training, evaluation, and safe checkpoint review. Covers the native 5.0 build and environment API, published 3.0.0... |
| `pybamm` | casa | MIT | si | Simulates lithium-ion battery charge, discharge and rest experiments with PyBaMM, records parameter-set provenance, checks mesh and solver sensitivity, and compares predicted voltage curves with measured cycling data. Use for SPM or DFN... |
| `pycalphad` | casa | MIT | si | Computes finite-temperature CALPHAD equilibria, phase fractions, and phase compositions from thermodynamic TDB databases using pycalphad. Use for alloy phase stability, equilibrium temperature sweeps, tie lines, lever-rule checks, or... |
| `pydeseq2` | casa | MIT | si | Performs bulk RNA-seq differential expression analysis with PyDESeq2, including count validation, formula designs, explicit contrasts, Wald tests, FDR correction, coefficient-matched LFC shrinkage, and result visualization. Use for... |
| `pydicom` | casa | MIT | si | Reads, inspects, writes, transforms, and preflights local DICOM datasets and pixel data. Applies to DICOM metadata, transfer syntaxes, compression plugins, frames, private elements, JSON, and bounded de-identification review. |
| `pyhealth` | casa | (non dichiarata) | no | Builds and validates PyHealth clinical machine-learning pipelines for EHR, signals, imaging, and medical codes. Use for PyHealth dataset loading, MIMIC-III/IV, eICU or OMOP prediction tasks, patient-level evaluation,... |
| `pylabrobot` | casa | MIT | si | Develops and reviews PyLabRobot lab-automation resources, liquid-handling plans, offline simulations, and supported-device integrations. Supports PyLabRobot protocols and API questions; keep physical execution behind an explicit... |
| `pymatgen` | casa | MIT | si | Analyzes, validates, converts, and transforms materials structures and computed materials data with pymatgen. Use for local phase diagrams, symmetry sensitivity, electronic-structure I/O, and bounded Materials Project queries. |
| `pymc` | casa | Apache License, Version 2.0 | si | Builds and checks Bayesian models with PyMC, including hierarchical models, NUTS MCMC, variational inference, mutable-data predictions, posterior predictive checks, diagnostics, and PSIS-LOO model comparison. Use for probabilistic... |
| `pymoo` | casa | Apache-2.0 | si | Solves and validates single-, multi-, and many-objective optimization with pymoo, including NSGA-II, NSGA-III, MOEA/D, constraints, Pareto approximations, reference directions, and ZDT/DTLZ benchmarks for engineering and research problems. |
| `pyopenms` | casa | 3 clause BSD | si | Processes mass spectrometry data with pyOpenMS. Supports proteomics and metabolomics workflows—feature detection, peptide/protein identification, label-free quantification, adduct/accurate-mass annotation, and complex LC-MS/MS... |
| `pysam` | casa | MIT | si | Provides Python/HTSlib workflows for genomic files. Used when reading, querying, filtering, or writing SAM/BAM/CRAM, VCF/BCF, FASTA/FASTQ, or tabix data with pysam, including pileup, coverage, indexing, and CRAM references. |
| `pytdc` | casa | MIT | si | Provides Therapeutics Data Commons workflows through PyTDC for registry discovery, dataset access, task-aware splits, evaluator metrics, benchmark groups, and bounded molecular-oracle scoring. Use when working with TDC therapeutic ML... |
| `pytorch-lightning` | casa | Apache-2.0 | si | Deep learning framework (PyTorch Lightning / lightning package). Organize PyTorch code into LightningModules, configure Trainers for multi-GPU/TPU, implement data pipelines, callbacks, logging (W&B, TensorBoard, MLflow), distributed... |
| `pyzotero` | casa | MIT | no | >- |
| `qiime2-amplicon` | casa | MIT | si | Processes paired-end 16S amplicon reads into QIIME 2 ASVs and taxonomy with retained artifact provenance. Checks paired FASTQ manifests, primer orientation diagnostics, predicted post-trimming overlap, sample IDs, runtime versions and... |
| `qiskit` | casa | Apache-2.0 | si | Builds, simulates, transpiles, and executes quantum circuits with Qiskit and IBM Quantum Runtime. Use for Qiskit 2.x circuits and operators, V2 Sampler or Estimator primitives, target-aware transpilation, local or noisy simulation, IBM... |
| `qutip` | casa | MIT | si | Simulate and audit closed and open quantum-system models with QuTiP 5, including deterministic, trajectory, steady-state, spectral, and phase-space workflows. Use for local quantum-dynamics work where physical assumptions, dimensions,... |
| `rdkit` | casa | BSD-3-Clause | si | Cheminformatics toolkit for fine-grained molecular control. SMILES/SDF parsing, descriptors (MW, LogP, TPSA), fingerprints, substructure search, 2D/3D generation, similarity, reactions. For standard workflows with simpler interface, use... |
| `relion` | casa | MIT | si | Validates and executes RELION single-particle cryo-EM refinement and half-map postprocessing. Supports STAR optics/acquisition checks, particle-stack consistency, gold-standard half sets, soft-mask validation, diagnostic Fourier shell... |
| `relsa-severity-assessment` | casa | MIT | si | Supports multivariate severity assessment and exploratory endpoint-time score forecasting for laboratory animal studies using the RELSA (RELative Severity Assessment) score and ARIMA-based foRcast forecasting. Use when combining welfare... |
| `research-grants` | casa | MIT | no | Supports research proposal preparation and review for NSF, NIH, DOE, DARPA, and Taiwan NSTC, including opportunity-specific requirements, aims, review criteria, budgets, broader impacts, forms, and resubmissions. Use for... |
| `research-lookup` | casa | MIT | si | Compiles current scholarly evidence for a scientific manuscript or research brief when the user explicitly asks to gather literature, references, background evidence, competing findings, or a manuscript research packet. Uses Parallel... |
| `rowan` | Rowan Science | Proprietaria | no | Rowan is a cloud-native molecular modeling and medicinal-chemistry workflow platform with a Python API. Use for pKa and macropKa prediction, conformer and tautomer ensembles, docking and analogue docking, protein-ligand cofolding, MSA... |
| `scanpy` | casa | BSD-3-Clause | si | Performs Scanpy single-cell RNA-seq QC, normalization, HVG selection, PCA/UMAP/t-SNE, clustering, exploratory marker ranking, pseudobulk preparation, visualization, and Seurat or SingleCellExperiment RDS conversion to h5ad. Applies to... |
| `scholar-evaluation` | casa | MIT | si | Provides qualitative-first, evidence-traceable developmental review of scholarly works and audit low-stakes research-assessment rubrics with optional local quality controls. Never use for ranking people or consequential decisions. |
| `scientific-brainstorming` | casa | MIT | si | Facilitates evidence-aware scientific ideation with independent generation, structured discussion, explicit assumptions, transparent evaluation, adversarial review, and decision logs. Use for early-stage research brainstorming or... |
| `scientific-critical-thinking` | casa | MIT | no | Evaluates scientific claims and evidence quality. Applies to experimental design validity, biases and confounders, statistical interpretation, evidence grading frameworks (GRADE, Cochrane Risk of Bias), and teaching critical analysis.... |
| `scientific-schematics` | casa | MIT | si | Generates scientific diagram drafts using Nano Banana 2 AI with smart iterative refinement. Uses Gemini 3.7 Flash for quality review. Refines when the review requests improvement, with at most two generations. Specialized in neural... |
| `scientific-slides` | casa | MIT | si | Builds slide decks and presentations for research talks. Used for making PowerPoint slides, conference presentations, seminar talks, research presentations, thesis defense slides, or any scientific talk. Provides slide structure, design... |
| `scientific-visualization` | casa | MIT | si | Creates and audits truthful, accessible, publication-ready scientific figures with Matplotlib, Seaborn, or Plotly. Use it for figure design, multi-panel layouts, uncertainty and missing-data displays, color/contrast review, image... |
| `scientific-writing` | casa | MIT | si | Drafts, revises, and audits scientific manuscripts or reports with explicit evidence provenance, reporting-guideline coverage, authorship accountability, confidentiality controls, and local consistency checks. Use for manuscript... |
| `scikit-bio` | casa | BSD-3-Clause | no | Biological data toolkit. Sequence analysis, alignments, phylogenetic trees, diversity metrics (alpha/beta, UniFrac), ordination (PCoA), PERMANOVA, FASTA/Newick I/O, for microbiome analysis. |
| `scikit-learn` | casa | BSD-3-Clause | si | Supports machine learning in Python with scikit-learn. Applies when working with supervised learning (classification, regression), unsupervised learning (clustering, dimensionality reduction), model evaluation, hyperparameter tuning,... |
| `scikit-survival` | casa | MIT | si | Builds, evaluates, and audits right-censored or competing-risk survival workflows with scikit-survival, including leakage-safe preprocessing, model selection, probability prediction, and censoring-aware metrics. |
| `scvelo` | Kuan-lin Huang | BSD-3-Clause | si | Performs RNA velocity analysis with scVelo from spliced and unspliced single-cell RNA counts. Fits deterministic or dynamical models, examines gene phase portraits, builds velocity graphs, estimates relative latent time, and ranks... |
| `scvi-tools` | casa | BSD-3-Clause | no | Fits probabilistic models for single-cell omics, including scVI batch integration, scANVI annotation, totalVI CITE-seq, MultiVI RNA/ATAC integration, and posterior differential expression. Use for generative modeling, reference mapping,... |
| `seaborn` | casa | BSD-3-Clause | no | Creates Seaborn statistical visualizations with pandas integration for distributions, relationships, categorical comparisons, regression displays, pair plots, and heatmaps. Supports function and objects interfaces with explicit... |
| `shap` | casa | MIT | si | Explain and audit machine-learning predictions with SHAP. Use for selecting SHAP explainers and maskers, computing and validating feature attributions, handling multi-output explanations, and producing local or global SHAP visualizations. |
| `simpy` | casa | MIT | si | Builds, inspects, tests, and analyzes bounded process-based discrete-event simulations with SimPy. Use for event scheduling, resource queues, interrupts, monitoring, independent replications, warm-up, and reproducible output analysis. |
| `stable-baselines3` | casa | MIT | si | Trains and evaluates single-agent reinforcement learning with Stable Baselines3 (PPO, SAC, DQN, TD3, DDPG, A2C), Gymnasium custom environments, vectorized rollouts, callbacks, and checkpoint normalization. Applies to reproducible RL... |
| `statistical-analysis` | casa | MIT | si | Guided statistical analysis for research data - test selection, assumption checking, effect sizes, power analysis, Bayesian alternatives, and APA-formatted reporting. Use whenever a user wants to compare groups, test a hypothesis,... |
| `statistical-power` | casa | MIT | si | Calculates sample sizes and statistical power for study planning. Applies when someone asks "how many subjects/samples/replicates do I need", wants an a priori power analysis, a minimum detectable effect (MDE), a power curve, or needs... |
| `statsmodels` | casa | BSD-3-Clause | no | Fits and diagnoses Python statistical models including OLS, GLM, discrete and mixed models, ARIMA and SARIMAX. Supports coefficient inference, marginal effects, model comparison and time series forecasting with explicit design and... |
| `sympy` | casa | https://github.com/sympy/sympy/blob/master/LICENSE | no | Performs exact symbolic mathematics with SymPy for algebra, calculus, equation solving, symbolic linear algebra, physics, and lambdify or LaTeX code generation. Use when a task needs symbolic results, explicit assumptions, or exact... |
| `tamarind` | Tamarind Bio | MIT | no | Provides access to a collection of open-source molecular design and structural biology tools on the Tamarind Bio platform, via its REST API or MCP server — no local GPUs required. Tamarind bundles popular open-source models for... |
| `tellurium` | casa | MIT | si | Simulates biochemical kinetic models from SBML or Antimony with Tellurium and libRoadRunner, checks model units, compares deterministic parameter perturbations, and exports and replays SBML plus SED-ML COMBINE archives. Use for... |
| `tiledbvcf` | Jeremy Leipzig | MIT | no | Stores and retrieves genomic variant calls with TileDB-VCF. Use for indexed single-sample VCF/BCF ingestion, incremental cohorts, region and sample queries, streaming results, allele statistics, QC, and VCF/BCF export locally or through... |
| `timesfm-forecasting` | Clayton Young / Superior Byte Works, LLC (@borealBytes) | Apache-2.0 | si | Performs zero-shot time-series forecasting with Google's TimesFM, including regular-grid CSV preparation, quantile forecasts, XReg covariates, and held-out evaluation. Uses the Apache-licensed TimesFM 2.5 checkpoint by default and... |
| `torch-geometric` | casa | MIT | no | Supports PyTorch Geometric (PyG) graph neural networks — node/link/graph classification, message passing (GCN, GAT, GraphSAGE, GIN), heterogeneous graphs, neighbor sampling, and custom datasets. Use when working with torch_geometric,... |
| `torchdrug` | casa | Apache-2.0 | no | Builds and troubleshoots TorchDrug 0.2.1 workflows for molecular graphs, property prediction, self-supervised pretraining, molecule generation, retrosynthesis, protein representation learning, and knowledge graph reasoning. Use when... |
| `transformers` | casa | Apache-2.0 | no | Hugging Face Transformers for loading Hub models, running pipeline inference, text generation, and Trainer fine-tuning on NLP, vision, audio, and multimodal tasks. Applies when working with AutoModel, pipelines, tokenizers, generation... |
| `treatment-plans` | casa | MIT | si | Formats and structurally validates local treatment-plan documentation after clinical decisions have already been supplied and verified by authorized licensed professionals. Use for source traceability, clinician-authored intervention... |
| `umap-learn` | casa | BSD-3-Clause | no | Applies UMAP-learn to nonlinear dimensionality reduction, 2D/3D embeddings, clustering preprocessing, supervised or semi-supervised UMAP, DensMAP, AlignedUMAP, and Parametric UMAP workflows. |
| `uncertainty-and-units` | casa | MIT | si | Tracks physical units and propagates measurement uncertainty in scientific calculations using pint and uncertainties. Use for unit conversion and dimensional checking, GUM uncertainty budgets, Type A and Type B evaluation, coverage... |
| `usfiscaldata` | casa | MIT | no | Queries the U.S. Treasury Fiscal Data REST API for federal financial data. No API key required. Use for national debt (Debt to the Penny), Daily Treasury Statements, Monthly Treasury Statements, Treasury securities auctions, interest... |
| `vaex` | casa | MIT | no | Processes large tabular scientific datasets with Vaex expressions, filtered views, streamed statistics, binned visualizations, and file conversion. Use for larger-than-RAM HDF5, Arrow, CSV, or Parquet analysis, virtual feature... |
| `venue-templates` | casa | MIT | si | Prepares journal manuscripts, conference papers, research posters, and grant documents using venue-specific formatting guidance and bundled LaTeX scaffolds. Supports selecting an official template, checking current page or anonymity... |
| `waypoint-bio` | casa | MIT | si | Supports work with Outpost Bio's open microbiome foundation models - the Waypoint checkpoints (Waypoint-6m, Waypoint-45m, Waypoint-170m), the Atlas pretraining corpus, the Compass eight-task benchmark, or the `waypoint` CLI from the... |
| `what-if-oracle` | AHK Strategies (ashrafkahoush-ux) | CC BY-NC-SA 4.0 | no | Supports structured what-if scenario analysis for research planning, experimental contingencies, and scientific project decisions. Explores favorable, reference, adverse, wild-card, contrarian, and second-order scenarios with explicit... |
| `zarr-python` | casa | MIT | no | Stores and queries chunked N-D scientific arrays with Zarr-Python 3, including codecs, sharding, S3/GCS storage, and NumPy/Dask/Xarray integration. Use for array layout, bounded I/O, format migration, or scientific metadata preservation. |

Copia letta in `C:/Users/Utente/AppData/Local/Temp/claude/E--template-claude-developing/644948a8-2f08-4e61-928e-65303aee7b29/scratchpad/kdense/repo`.
