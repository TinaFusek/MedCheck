import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from neo4j import GraphDatabase
import anthropic
from neo4j_service import (
    get_drug_interactions,
    get_drugs_for_symptom,
    get_enhancers,
    get_drug_details
)

load_dotenv()

# ── Config from .env ──────────────────────────────────────────────────────────
NEO4J_URI  = os.getenv("NEO4J_URI",      "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="MedCheck API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request models ────────────────────────────────────────────────────────────
class CheckRequest(BaseModel):
    drugs: list[str]

class SymptomRequest(BaseModel):
    symptom: str

class GraphRAGRequest(BaseModel):
    system: str = ""
    messages: list[dict]

class CypherRequest(BaseModel):
    query: str
    params: dict = {}

# ── Static ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return FileResponse("index.html")

# ── Original endpoints ────────────────────────────────────────────────────────
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
                    "type":   record["rel_type"],
                    "risk":   record["risk"]
                })
        return {"nodes": [{"id": n} for n in nodes], "links": links}

@app.get("/pagerank")
def pagerank():
    with driver.session() as session:
        session.run("CALL gds.graph.drop('drugGraph', false)")
        session.run("""
            CALL gds.graph.project('drugGraph', 'Drug', 'INTERACTS_WITH')
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
                {"drug": r["drug_name"] or r["drug_id"], "score": round(r["score"], 4)}
                for r in result
            ]
        }

# ── GraphRAG — Claude cez backend (nie priamo z browsera) ─────────────────────
@app.post("/graphrag")
def graphrag(request: GraphRAGRequest):
    try:
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=request.system,
            messages=request.messages
        )
        return {"text": response.content[0].text}
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Cypher proxy — Neo4j bez credentials vo frontende ────────────────────────
@app.post("/cypher")
def cypher_proxy(request: CypherRequest):
    try:
        with driver.session() as session:
            result = session.run(request.query, **request.params)
            columns = list(result.keys())
            rows = [dict(zip(columns, record.values())) for record in result]
            return {
                "result": {
                    "columns": columns,
                    "data": [{"row": list(r.values())} for r in rows]
                }
            }
    except Exception as e:
        return {"error": str(e)}
