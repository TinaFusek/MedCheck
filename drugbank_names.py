import requests
import time
from neo4j import GraphDatabase

URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "..."  # zmeň na svoje

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def get_drugbank_ids():
    with driver.session() as session:
        result = session.run("""
            MATCH (d:Drug)
            WHERE d.name STARTS WITH 'DB' AND d.display_name IS NULL
            RETURN d.name AS id
            LIMIT 100
        """)
        return [r["id"] for r in result]

def lookup_name(db_id):
    # PubChem - hladanie cez DrugBank ID ako synonym
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{db_id}/property/IUPACName,Title/JSON"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            props = data.get('PropertyTable', {}).get('Properties', [])
            if props:
                return props[0].get('Title')
    except Exception as e:
        print(f"  Error: {e}")
    return None

def update_name(db_id, name):
    with driver.session() as session:
        session.run("""
            MATCH (d:Drug {name: $id})
            SET d.display_name = $display_name
        """, id=db_id, display_name=name)

def run():
    ids = get_drugbank_ids()
    print(f"Found {len(ids)} unmapped DrugBank IDs\n")
    found = 0
    for db_id in ids:
        name = lookup_name(db_id)
        if name:
            update_name(db_id, name)
            print(f"  {db_id} -> {name}")
            found += 1
        else:
            print(f"  {db_id} -> not found")
        time.sleep(0.3)
    print(f"\nDone! Mapped {found}/{len(ids)}")

if __name__ == "__main__":
    run()
