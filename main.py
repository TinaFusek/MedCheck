from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from neo4j import GraphDatabase
from neo4j_service import (
    get_drug_interactions,
    get_drugs_for_symptom,
    get_enhancers,
    get_drug_details
)

URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "Ad4m+5amo12_Ad4m+5amo12"  # zmeň na svoje

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

app = FastAPI(title="MedCheck API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CheckRequest(BaseModel):
    drugs: list[str]

class SymptomRequest(BaseModel):
    symptom: str

@app.get("/")
def root():
    return FileResponse("index.html")

@app.post("/check")
def check_interactions(request: CheckRequest):
    results = get_drug_interactions(request.drugs)
    return {"results": results}

@app.post("/symptom")
def symptom_check(request: SymptomRequest):
    results = get_drugs_for_symptom(request.symptom)
    return {"results": results}

@app.get("/enhancers/{drug_name}")
def enhancers(drug_name: str):
    results = get_enhancers(drug_name)
    return {"results": results}

@app.get("/drug/{drug_name}")
def drug_details(drug_name: str):
    results = get_drug_details(drug_name)
    return {"results": results}

@app.get("/graph/{drug_name}")
def drug_graph(drug_name: str):
    with driver.session() as session:
        result = session.run("""
            MATCH (d:Drug)
            WHERE toLower(d.name) = toLower($name)
               OR toLower(d.display_name) = toLower($name)
            OPTIONAL MATCH (d)-[r]->(d2:Drug)
            RETURN coalesce(d.display_name, d.name) AS source,
                   type(r) AS rel_type,
                   coalesce(d2.display_name, d2.name) AS target,
                   r.risk AS risk
        """, name=drug_name)
        links = []
        nodes = set()
        for record in result:
            if record["target"]:
                nodes.add(record["source"])
                nodes.add(record["target"])
                links.append({
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["rel_type"],
                    "risk": record["risk"]
                })
        return {
            "nodes": [{"id": n} for n in nodes],
            "links": links
        }

@app.get("/pagerank")
def pagerank():
    with driver.session() as session:
        # Vytvor graph projection
        session.run("""
            CALL gds.graph.drop('drugGraph', false)
        """)
        session.run("""
            CALL gds.graph.project(
                'drugGraph',
                'Drug',
                'INTERACTS_WITH'
            )
        """)
        result = session.run("""
            CALL gds.pageRank.stream('drugGraph')
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS drug_id,
                   gds.util.asNode(nodeId).display_name AS drug_name,
                   score
            ORDER BY score DESC
            LIMIT 15
        """)
        return {
            "results": [
                {
                    "drug": r["drug_name"] or r["drug_id"],
                    "score": round(r["score"], 4)
                }
                for r in result
            ]
        }