import csv
from neo4j import GraphDatabase

URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "...Ad4m+5amo12_Ad4m+5amo12"  # zmeň na svoje

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def import_mendeley(filepath):
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get('drug1_id') and row.get('drug2_id') and
                row.get('drug1_name') and row.get('drug2_name')):
                rows.append(row)

    print(f"Loaded {len(rows)} valid interactions\n")

    batch_size = 500
    total = 0

    with driver.session() as session:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            session.run("""
                UNWIND $rows AS row
                MERGE (d1:Drug {name: row.drug1_id})
                ON CREATE SET d1.display_name = row.drug1_name
                MERGE (d2:Drug {name: row.drug2_id})
                ON CREATE SET d2.display_name = row.drug2_name
                MERGE (d1)-[:INTERACTS_WITH {
                    type: row.interaction_type,
                    source: 'Mendeley_DrugBank'
                }]->(d2)
            """, rows=[dict(r) for r in batch])
            total += len(batch)
            print(f"  Imported {total}/{len(rows)}...")

    print("\nDone!")

if __name__ == "__main__":
    import_mendeley("DDI_data.csv")
