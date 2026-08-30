import csv
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI      = os.getenv("NEO4J_URI",      "neo4j://localhost:7687")
USERNAME = os.getenv("NEO4J_USER",     "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run():
    with open('drugbank_mapping.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loading {len(rows)} mappings...")
    with driver.session() as session:
        for row in rows:
            session.run("""
                MATCH (d:Drug {name: $id})
                SET d.display_name = $name
            """, id=row['drugbank_id'], name=row['name'])
            print(f"  {row['drugbank_id']} -> {row['name']}")

    print("Done!")

if __name__ == "__main__":
    run()