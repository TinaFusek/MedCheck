import gzip
import csv
from neo4j import GraphDatabase

URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "Ad4m+5amo12_Ad4m+5amo12"  # zmeň na svoje

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def import_snap(filepath):
    interactions = []

    with open(filepath, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if row[0].startswith('#'):
                continue
            if len(row) >= 2:
                interactions.append((row[0].strip(), row[1].strip()))

    print(f"Loaded {len(interactions)} interactions from file")

    with driver.session() as session:
        batch_size = 500
        total = 0
        for i in range(0, len(interactions), batch_size):
            batch = interactions[i:i+batch_size]
            session.run("""
                UNWIND $pairs AS pair
                MERGE (d1:Drug {name: pair[0]})
                MERGE (d2:Drug {name: pair[1]})
                MERGE (d1)-[:INTERACTS_WITH {source: 'SNAP_DrugBank'}]->(d2)
            """, pairs=[[a, b] for a, b in batch])
            total += len(batch)
            print(f"  Imported {total}/{len(interactions)}...")

    print("Done!")

if __name__ == "__main__":
    import_snap("ChCh-Miner_durgbank-chem-chem.tsv")