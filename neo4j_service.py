from neo4j import GraphDatabase

URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "Ad4m+5amo12_Ad4m+5amo12"  

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def get_drug_interactions(drug_names: list):
    query = """
    UNWIND $names AS drugName
    MATCH (d:Drug)
    WHERE toLower(d.name) = toLower(drugName)
    OPTIONAL MATCH (d)-[r:INTERACTS_WITH|CONTRAINDICATED_WITH|REDUCES_EFFICACY]->(d2:Drug)
    OPTIONAL MATCH (d)-[s:SAFE_WITH]->(d3:Drug)
    OPTIONAL MATCH (d)-[e:ANTAGONIST_OF]->(d4:Drug)
    RETURN d.name AS drug,
           collect(DISTINCT {drug: d2.name, type: type(r), risk: r.risk, reason: r.reason, effect: r.effect}) AS dangers,
           collect(DISTINCT {drug: d3.name, note: s.note}) AS safe,
           collect(DISTINCT {drug: d4.name}) AS antagonists
    """
    with driver.session() as session:
        result = session.run(query, names=drug_names)
        return [record.data() for record in result]

def get_drugs_for_symptom(symptom: str):
    query = """
    MATCH (d:Drug)-[:TREATS]->(i:Indication)
    WHERE toLower(i.name) CONTAINS toLower($symptom)
    RETURN d.name AS drug, i.name AS indication,
           d.prescription AS prescription
    ORDER BY d.prescription ASC
    """
    with driver.session() as session:
        result = session.run(query, symptom=symptom)
        return [record.data() for record in result]

def get_enhancers(drug_name: str):
    query = """
    MATCH (d:Drug)
    WHERE toLower(d.name) = toLower($name)
    OPTIONAL MATCH (d)-[r:SAFE_WITH]->(d2:Drug)
    WHERE (d2)-[:BELONGS_TO]->(:Category {name: 'Biohacking'})
    RETURN d2.name AS enhancer, r.note AS effect
    """
    with driver.session() as session:
        result = session.run(query, name=drug_name)
        return [record.data() for record in result]

def get_drug_details(drug_name: str):
    query = """
    MATCH (d:Drug)
    WHERE toLower(d.name) = toLower($name)
    OPTIONAL MATCH (d)-[:BELONGS_TO]->(c:Category)
    OPTIONAL MATCH (d)-[:HAS_MECHANISM]->(m:Mechanism)
    OPTIONAL MATCH (d)-[:TREATS]->(i:Indication)
    RETURN d.name AS name,
           d.chembl_id AS chembl_id,
           d.molecular_weight AS molecular_weight,
           d.formula AS formula,
           d.prescription AS prescription,
           collect(DISTINCT c.name) AS categories,
           collect(DISTINCT m.name) AS mechanisms,
           collect(DISTINCT i.name) AS indications
    """
    with driver.session() as session:
        result = session.run(query, name=drug_name)
        return [record.data() for record in result]