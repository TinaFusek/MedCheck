# MedCheck 💊
**Drug Interaction & Contraindication Checker — powered by Neo4j Knowledge Graph**

Clinical reference tool for drug interaction analysis, discrepancy detection, and GraphRAG-powered AI analysis.

---

## Features

- **Interaction Checker** — check drug combinations against 271k+ interactions
- **Symptom Lookup** — find drugs indicated for a condition
- **Efficacy Enhancers** — safe supplement combinations
- **Discrepancy Detector** — GDS + Cypher anomaly detection in the KG
- **GraphRAG Analyst** — Claude AI analysis over Neo4j subgraphs (3 modes)

## Data Sources

| Source | Content |
|---|---|
| DrugBank (via Mendeley) | DDI interactions with risk levels |
| SNAP BioData | ChCh-Miner drug-drug interactions |
| ChEMBL API | Molecular properties, ChEMBL IDs |

## Stack

- **Database**: Neo4j Desktop + Graph Data Science (GDS) plugin
- **Backend**: FastAPI + Python
- **Frontend**: HTML/CSS/JS (single file)
- **AI**: Anthropic Claude (GraphRAG layer)

---

## Setup

### 1. Clone
```bash
git clone https://github.com/YOUR_USERNAME/MedCheck.git
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

### 4. Neo4j Desktop
- Install [Neo4j Desktop](https://neo4j.com/download/)
- Add **Graph Data Science Library** plugin
- Start your database
- Import data using the scripts below

### 5. Run
```bash
uvicorn main:app --reload
# Open: http://localhost:8000
```

---

## Data Import (run in order)

```bash
# 1. DrugBank interactions (Mendeley dataset)
python mendeley_import.py

# 2. SNAP drug-drug interactions
python snap_import.py

# 3. Resolve DrugBank IDs → display names
python load_mapping.py
python drugbank_names.py

# 4. Enrich with ChEMBL molecular data
python chembl_import.py

# 5. GDS analysis + visualization
python gds_analysis.py
python visualize.py
```

---

## Project Structure

```
MedCheck/
├── main.py              # FastAPI backend
├── neo4j_service.py     # Cypher query functions
├── graphrag_pipeline.py # GraphRAG + Claude AI
├── chembl_import.py     # ChEMBL data enrichment
├── mendeley_import.py   # DDI dataset import
├── snap_import.py       # SNAP BioData import
├── drugbank_names.py    # DrugBank ID → name resolver
├── load_mapping.py      # CSV mapping loader
├── gds_analysis.py      # GDS PageRank, Betweenness, Louvain
├── visualize.py         # Matplotlib charts
├── index.html           # Frontend UI
├── requirements.txt
├── .env.example         # API key template
└── .gitignore
```

---

> MedCheck is for informational and educational purposes only.
> Always consult a licensed healthcare professional before making medical decisions.
