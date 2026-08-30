# Data sources

This repository ships no datasets. Everything below is downloaded by the user
into a local `data/` directory, which is gitignored.

Each entry records what was verified and when. Where a source publishes no
named licence, that is recorded as a finding — not left blank.

---

## 1. DDI dataset (via Mendeley Data)

| | |
|---|---|
| **File** | `data/DDI_data.csv` |
| **Download** | TODO — paste the exact Mendeley Data dataset URL |
| **Version / DOI** | TODO |
| **Downloaded on** | TODO — YYYY-MM-DD |
| **Licence** | TODO — Mendeley Data shows the licence on the dataset page, usually CC BY 4.0; copy the exact name shown |
| **Redistribution allowed?** | TODO |
| **Upstream origin** | DrugBank |

Drug–drug interaction pairs with risk levels.

---

## 2. SNAP BioData — ChCh-Miner

| | |
|---|---|
| **File** | `data/ChCh-Miner_durgbank-chem-chem.tsv` |
| **Download** | https://snap.stanford.edu/biodata/datasets/10001/10001-ChCh-Miner.html |
| **Version** | as published on the BioSNAP page (no version identifier given) |
| **Verified on** | 2026-08-30 |
| **Licence** | **No named licence published.** The BioSNAP dataset pages state a citation requirement but do not name a licence. Note: the BSD licence on snap.stanford.edu applies to the SNAP *software library*, not to the BioSNAP *datasets* — these are different things. |
| **Redistribution** | Not done. Absent a named licence, this project cites the source and does not redistribute the raw file. |
| **Upstream origin** | The BioSNAP page states the interactions are extracted from drug labels and scientific publications. The filename (`drugbank-chem-chem`) indicates DrugBank. This discrepancy is unresolved and is recorded here as-is. |

**Citation:**
> Marinka Zitnik, Rok Sosič, Sagar Maheshwari, Jure Leskovec.
> *BioSNAP Datasets: Stanford Biomedical Network Dataset Collection.*
> http://snap.stanford.edu/biodata, August 2018.

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
| **Access** | ChEMBL web API — fetched at runtime by `chembl_import.py`; no local file |
| **Licence** | CC BY-SA 3.0 |
| **Verified on** | 2026-08-30 |
| **Citation** | Zdrazil et al., *The ChEMBL Database in 2023*, Nucleic Acids Research |

Molecular properties and ChEMBL IDs.

---

## 5. Unresolved files

`DDI_types.xlsx` and `DDI_types_merged.xlsx` were present in an earlier version
of this repository. Their provenance is not documented and it is not confirmed
whether any import script reads them. To be resolved: identify the source, or
confirm they are unused and drop them.

---

## Licence lineage — read before deploying

Sources 1 and 3 derive from **DrugBank**; source 2 probably does too (see the
discrepancy noted above). There is no independent interaction layer in this
graph: the interaction set has a single licence lineage.

DrugBank's free licence covers academic and non-commercial use only. A publicly
deployed application requires a commercial licence. This repository is a
personal portfolio project and is not deployed.

If an independent or more permissive interaction layer is ever needed,
candidates worth evaluating are DDInter, DrugCentral, and RxNorm/RxNav. Each
needs the same treatment as above — and note that for DDInter the CC BY-NC 4.0
notice belongs to the *Nucleic Acids Research article*, not to the database;
the database's own terms are on its About page.
