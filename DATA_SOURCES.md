# Data sources

This repository ships no datasets. Everything below is downloaded by the user
into a local `data/` directory, which is gitignored.

**Fill in the blanks marked `TODO` before relying on this file.** An unverified
licence line is worse than no licence line — it looks like a claim.

---

## 1. DDI dataset (via Mendeley Data)

| | |
|---|---|
| **File** | `data/DDI_data.csv` |
| **Download** | TODO — paste the exact Mendeley dataset URL |
| **Version / DOI** | TODO |
| **Downloaded on** | TODO — YYYY-MM-DD |
| **Licence** | TODO — read the licence shown on the Mendeley dataset page |
| **Redistribution allowed?** | TODO — yes / no |
| **Upstream origin** | DrugBank |

Contains drug–drug interaction pairs with risk levels.

---

## 2. SNAP BioData — ChCh-Miner

| | |
|---|---|
| **File** | `data/ChCh-Miner_durgbank-chem-chem.tsv` |
| **Download** | http://snap.stanford.edu/biodata/ |
| **Version** | TODO |
| **Downloaded on** | TODO |
| **Licence** | TODO — see SNAP BioData terms |
| **Redistribution allowed?** | TODO |
| **Upstream origin** | DrugBank (the filename says so: `drugbank-chem-chem`) |

Drug–drug interaction pairs, no severity annotation.

---

## 3. DrugBank ID → name mapping

| | |
|---|---|
| **File** | `data/drugbank_mapping.csv` |
| **Download** | TODO — where did this come from? |
| **Licence** | TODO |
| **Redistribution allowed?** | TODO |

---

## 4. ChEMBL

| | |
|---|---|
| **Access** | ChEMBL web API — fetched at runtime by `chembl_import.py` |
| **Licence** | CC BY-SA 3.0 |
| **Citation** | Zdrazil et al., *The ChEMBL Database in 2023*, Nucleic Acids Research |

Molecular properties and ChEMBL IDs. No local file needed.

---

## Licence lineage — read this before deploying anything

Sources 1, 2 and 3 all derive from **DrugBank**. There is no independent
interaction layer in this graph: the entire interaction set has one licence
lineage.

DrugBank's free licence covers academic and non-commercial use only. A
publicly deployed application requires a commercial licence. This repository
is a personal portfolio project and is not deployed.

If an independent or more permissive interaction layer is ever needed,
candidates worth evaluating are DDInter, DrugCentral, and RxNorm/RxNav —
each with its own terms that would need the same treatment as above.
