import requests
import time
from neo4j import GraphDatabase

URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "Ad4m+5amo12_Ad4m+5amo12"  # zmeň na svoje

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"

def get_drugs_without_chembl():
    with driver.session() as session:
        result = session.run("""
            MATCH (d:Drug)
            WHERE d.chembl_id IS NULL
            RETURN d.name AS name
        """)
        return [r["name"] for r in result]

def search_chembl(drug_name, retries=3):
    url = f"{CHEMBL_API}/molecule/search?q={drug_name}&format=json&limit=1"
    for attempt in range(retries):
        try:
            res = requests.get(url, timeout=15)
            if res.status_code != 200:
                return None
            data = res.json()
            molecules = data.get("molecules", [])
            if not molecules:
                return None
            m = molecules[0]
            props = m.get("molecule_properties") or {}
            return {
                "chembl_id": m.get("molecule_chembl_id"),
                "molecular_weight": props.get("full_mwt"),
                "formula": props.get("full_molformula"),
                "alogp": props.get("alogp"),
                "synonyms": [s["molecule_synonym"] for s in
                             (m.get("molecule_synonyms") or [])[:3]]
            }
        except Exception as e:
            print(f"  Attempt {attempt+1}/{retries} failed: {e}")
            time.sleep(3)
    return None

def update_drug_in_neo4j(name, data):
    with driver.session() as session:
        session.run("""
            MATCH (d:Drug {name: $name})
            SET d.chembl_id = $chembl_id,
                d.molecular_weight = $molecular_weight,
                d.formula = $formula,
                d.alogp = $alogp,
                d.synonyms = $synonyms
        """, name=name, **data)

def run_import():
    drugs = get_drugs_without_chembl()
    print(f"Drugs without ChEMBL data: {len(drugs)}\n")

    skip = ['Chlorella', 'Spirulina', 'Wheatgrass']

    for drug in drugs:
        if drug in skip:
            print(f"Skipping (food/supplement): {drug}")
            continue

        print(f"Fetching: {drug}...")
        data = search_chembl(drug)
        if data and data["chembl_id"]:
            update_drug_in_neo4j(drug, data)
            print(f"  OK — {data['chembl_id']} | MW: {data['molecular_weight']} | {data['formula']}")
        else:
            print(f"  Not found in ChEMBL")

        time.sleep(1)

    print("\nDone!")

if __name__ == "__main__":
    run_import()