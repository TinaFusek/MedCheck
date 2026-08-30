# MedCheck 💊

**Drug Interaction & Contraindication Explorer — powered by a Neo4j Knowledge Graph**

An educational reference tool for exploring drug interactions, detecting
inconsistencies in the graph, and running GraphRAG-powered analysis over
Neo4j subgraphs.

---

<img width="1920" height="5037" alt="medcheck" src="https://github.com/user-attachments/assets/54a37df4-fe14-437d-b942-c7bcae5aa177" />

---

## Features

- **Interaction Checker** — check drug combinations against the loaded interaction set
- **Symptom Lookup** — find drugs indicated for a condition
- **Efficacy Enhancers** — supplement combinations
- **Discrepancy Detector** — GDS + Cypher anomaly detection in the KG
- **GraphRAG Analyst** — Claude analysis over Neo4j subgraphs (3 modes)

## Data

**This repository contains code only. No datasets are redistributed here.**
You download the sources yourself and place them in `data/`, which is
gitignored. See [`DATA_SOURCES.md`](DATA_SOURCES.md) for exact download
locations, versions, and licence terms.

| Source | Content | Licence |
|---|---|---|
| DDI dataset (Mendeley) | Drug–drug interactions with risk levels | see `DATA_SOURCES.md` |
| SNAP BioData — ChCh-Miner | Drug–drug interaction pairs | see `DATA_SOURCES.md` |
| ChEMBL API | Molecular properties, ChEMBL IDs | CC BY-SA 3.0 |

> Note on lineage: both interaction sources above are DrugBank-derived, so the
> interaction layer has a single licence lineage. DrugBank's free licence
> covers academic / non-commercial use only. Check the terms before doing
> anything beyond local, personal use.

## Stack

- **Database**: Neo4j Desktop + Graph Data Science (GDS) plugin
- **Backend**: FastAPI + Python
- **Frontend**: HTML/CSS/JS (single file)
- **AI**: Anthropic Claude (GraphRAG layer)

---

## Setup

### 1. Clone
```bash
git clone https://github.com/TinaFusek/MedCheck.git
cd MedCheck
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY and Neo4j password
```

### 4. Download the data
Create a `data/` directory and download the source files into it, following
[`DATA_SOURCES.md`](DATA_SOURCES.md). The import scripts expect:

```
data/
├── DDI_data.csv                        # Mendeley DDI dataset
├── ChCh-Miner_durgbank-chem-chem.tsv   # SNAP BioData
└── drugbank_mapping.csv                # DrugBank ID → name mapping
```

### 5. Neo4j Desktop
- Install [Neo4j Desktop](https://neo4j.com/download/)
- Add the **Graph Data Science Library** plugin
- Start your database

### 6. Import (run in order)
```bash
python mendeley_import.py     # DDI interactions
python snap_import.py         # SNAP drug-drug interactions
python load_mapping.py        # load ID → name mapping
python drugbank_names.py      # resolve IDs to display names
python chembl_import.py       # enrich with ChEMBL molecular data
python gds_analysis.py        # GDS PageRank, Betweenness, Louvain
python visualize.py           # charts
```

### 7. Run
```bash
uvicorn main:app --reload
# Open: http://localhost:8000
```

---

## Project Structure

```
MedCheck/
├── main.py              # FastAPI backend
├── neo4j_service.py     # Cypher query functions
├── graphrag_pipeline.py # GraphRAG + Claude
├── chembl_import.py     # ChEMBL data enrichment
├── mendeley_import.py   # DDI dataset import
├── snap_import.py       # SNAP BioData import
├── drugbank_names.py    # DrugBank ID → name resolver
├── load_mapping.py      # CSV mapping loader
├── gds_analysis.py      # GDS PageRank, Betweenness, Louvain
├── visualize.py         # Matplotlib charts
├── index.html           # Frontend UI
├── requirements.txt
├── DATA_SOURCES.md      # where the data comes from, and under what terms
├── LICENSE              # applies to the code in this repository
├── .env.example
└── .gitignore
```

`data/` is created by you at setup time and is gitignored.

---

## Licence

The code in this repository is released under the MIT License (see `LICENSE`).
The datasets are **not** covered by it — each carries its own terms, listed in
`DATA_SOURCES.md`.

---

> MedCheck is for informational and educational purposes only. It is not a
> medical device and does not provide medical advice. Always consult a
> licensed healthcare professional before making medical decisions.
