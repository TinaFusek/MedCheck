"""
MedCheck GraphRAG Pipeline
==========================
Neo4j Knowledge Graph + Claude (Anthropic) = narrative analysis

Requirements:
    pip install neo4j anthropic python-dotenv

Setup:
    cp .env.example .env
    # Add ANTHROPIC_API_KEY and NEO4J_PASSWORD to .env

Usage:
    python graphrag_pipeline.py
"""

import json
import os
from neo4j import GraphDatabase
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ── Config — reads from .env ──────────────────────────────────────────────────
NEO4J_URI  = os.getenv("NEO4J_URI",      "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "")

CLAUDE_MODEL = "claude-sonnet-4-6"

# ── Neo4j driver ──────────────────────────────────────────────────────────────
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
claude = anthropic.Anthropic()    # reads ANTHROPIC_API_KEY from .env


# ══════════════════════════════════════════════════════════════════════════════
# 1. CYPHER QUERIES — structured retrieval
# ══════════════════════════════════════════════════════════════════════════════

def get_drug_subgraph(drug_name: str) -> dict:
    """Retrieve full subgraph for a drug from Neo4j."""
    with driver.session() as session:
        result = session.run("""
            MATCH (d:Drug {name: $name})
            OPTIONAL MATCH (d)-[r1:INTERACTS_WITH]->(b:Drug)
            OPTIONAL MATCH (d)-[r2:CONTRAINDICATED_WITH]->(c:Drug)
            OPTIONAL MATCH (d)-[r3:SAFE_WITH]->(s:Drug)
            OPTIONAL MATCH (d)-[:BELONGS_TO]->(cls:DrugClass)
            OPTIONAL MATCH (d)-[:INDICATED_FOR]->(sym:Symptom)
            RETURN
                d.name AS drug,
                collect(DISTINCT {
                    drug: b.name,
                    severity: r1.severity,
                    description: r1.description
                }) AS interactions,
                collect(DISTINCT {
                    drug: c.name,
                    reason: r2.reason
                }) AS contraindications,
                collect(DISTINCT {
                    drug: s.name,
                    note: r3.note
                }) AS safe_combinations,
                collect(DISTINCT cls.name) AS classes,
                collect(DISTINCT sym.name) AS indications
        """, name=drug_name)
        row = result.single()
        return dict(row) if row else {}


def get_discrepancies() -> list:
    """Find all discrepancies in the KG via Cypher."""
    with driver.session() as session:
        discrepancies = []

        # Rule 1: SAFE + CONTRAINDICATED on same pair
        r1 = session.run("""
            MATCH (a)-[:SAFE_WITH]->(b)
            MATCH (a)-[:CONTRAINDICATED_WITH]->(b)
            RETURN
                'RELATIONSHIP_CONFLICT' AS type,
                a.name AS entity_a,
                b.name AS entity_b,
                'Drug is both SAFE_WITH and CONTRAINDICATED_WITH the same drug' AS detail
        """)
        discrepancies.extend([dict(r) for r in r1])

        # Rule 2: Drug without class
        r2 = session.run("""
            MATCH (d:Drug)
            WHERE NOT (d)-[:BELONGS_TO]->()
            RETURN
                'MISSING_CLASS' AS type,
                d.name AS entity_a,
                null AS entity_b,
                'Drug has no DrugClass assignment' AS detail
        """)
        discrepancies.extend([dict(r) for r in r2])

        # Rule 3: Orphaned nodes
        r3 = session.run("""
            MATCH (n)
            WHERE NOT (n)--() AND (n:Drug OR n:Supplement)
            RETURN
                'ORPHANED_NODE' AS type,
                coalesce(n.name, toString(id(n))) AS entity_a,
                null AS entity_b,
                'Node has no relationships — isolated in the graph' AS detail
            LIMIT 10
        """)
        discrepancies.extend([dict(r) for r in r3])

        # Rule 4: Duplicate names
        r4 = session.run("""
            MATCH (n)
            WHERE n.name IS NOT NULL
            WITH n.name AS name, labels(n)[0] AS label, count(*) AS cnt
            WHERE cnt > 1
            RETURN
                'DUPLICATE_NAME' AS type,
                name AS entity_a,
                toString(cnt) + ' nodes' AS entity_b,
                'Multiple nodes share the same name' AS detail
            LIMIT 10
        """)
        discrepancies.extend([dict(r) for r in r4])

        return discrepancies


def get_symptom_drugs(symptom: str) -> list:
    """Retrieve drugs indicated for a symptom."""
    with driver.session() as session:
        result = session.run("""
            MATCH (d:Drug)-[:INDICATED_FOR]->(s:Symptom)
            WHERE toLower(s.name) CONTAINS toLower($symptom)
            OPTIONAL MATCH (d)-[:BELONGS_TO]->(cls:DrugClass)
            RETURN
                d.name AS drug,
                s.name AS symptom,
                collect(DISTINCT cls.name) AS classes,
                d.otc AS otc
            ORDER BY d.name
        """, symptom=symptom)
        return [dict(r) for r in result]


# ══════════════════════════════════════════════════════════════════════════════
# 2. SUBGRAPH SERIALIZATION — KG → text context for LLM
# ══════════════════════════════════════════════════════════════════════════════

def serialize_drug_subgraph(subgraph: dict) -> str:
    """Convert Neo4j subgraph dict to readable text for LLM context."""
    if not subgraph or not subgraph.get("drug"):
        return "No data found for this drug in the knowledge graph."

    lines = [f"KNOWLEDGE GRAPH DATA FOR: {subgraph['drug']}"]
    lines.append("=" * 50)

    if subgraph.get("classes"):
        classes = [c for c in subgraph["classes"] if c]
        if classes:
            lines.append(f"Drug Class: {', '.join(classes)}")

    if subgraph.get("indications"):
        indications = [i for i in subgraph["indications"] if i]
        if indications:
            lines.append(f"Indicated for: {', '.join(indications)}")

    interactions = [i for i in subgraph.get("interactions", []) if i.get("drug")]
    if interactions:
        lines.append("\nINTERACTIONS:")
        for i in interactions:
            lines.append(
                f"  - INTERACTS WITH {i['drug']} "
                f"[severity: {i.get('severity','unknown')}] "
                f"— {i.get('description','')}"
            )

    contraindications = [c for c in subgraph.get("contraindications", []) if c.get("drug")]
    if contraindications:
        lines.append("\nCONTRAINDICATIONS:")
        for c in contraindications:
            lines.append(
                f"  - CONTRAINDICATED WITH {c['drug']} "
                f"— {c.get('reason','')}"
            )

    safe_combos = [s for s in subgraph.get("safe_combinations", []) if s.get("drug")]
    if safe_combos:
        lines.append("\nSAFE COMBINATIONS:")
        for s in safe_combos:
            lines.append(f"  - SAFE WITH {s['drug']} — {s.get('note','')}")

    return "\n".join(lines)


def serialize_discrepancies(discrepancies: list) -> str:
    """Convert discrepancy list to text for LLM context."""
    if not discrepancies:
        return "No discrepancies found in the Knowledge Graph."

    lines = [f"KNOWLEDGE GRAPH DISCREPANCIES ({len(discrepancies)} found)"]
    lines.append("=" * 50)

    for d in discrepancies:
        line = f"[{d['type']}] {d['entity_a']}"
        if d.get("entity_b"):
            line += f" ↔ {d['entity_b']}"
        line += f"\n  Detail: {d['detail']}"
        lines.append(line)

    return "\n".join(lines)


def serialize_symptom_drugs(drugs: list, symptom: str) -> str:
    """Convert drug list to text for LLM context."""
    if not drugs:
        return f"No drugs found for symptom: {symptom}"

    lines = [f"DRUGS INDICATED FOR: {symptom.upper()}"]
    lines.append("=" * 50)
    for d in drugs:
        otc = "OTC" if d.get("otc") else "Prescription"
        classes = ", ".join(d.get("classes") or []) or "unclassified"
        lines.append(f"  - {d['drug']} [{otc}] | Class: {classes}")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# 3. LLM CALLS — GraphRAG: subgraph → narrative
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a clinical knowledge graph analyst.
You receive structured data extracted from a Neo4j Knowledge Graph about drugs,
their interactions, contraindications, and safe combinations.
Your job is to analyze this data and provide clear, accurate, clinically relevant insights.
Be concise but thorough. Flag any data quality issues or conflicts you notice.
Always note that this is for informational purposes only."""


def llm_analyze_drug(drug_name: str) -> str:
    """GraphRAG: fetch subgraph → LLM narrative analysis."""
    # Step 1: Cypher retrieval
    subgraph = get_drug_subgraph(drug_name)

    # Step 2: Serialize to text context
    context = serialize_drug_subgraph(subgraph)

    # Step 3: LLM call with subgraph as context
    response = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""{context}

Based on this Knowledge Graph data, provide:
1. A brief clinical summary of {drug_name}
2. Key interaction risks (highlight HIGH/MEDIUM severity)
3. Any data quality issues or conflicts in the graph
4. Recommended safe combinations
5. Clinical recommendation

Keep it concise and clinically focused."""
        }]
    )
    return response.content[0].text


def llm_analyze_discrepancies() -> str:
    """GraphRAG: fetch all discrepancies → LLM audit report."""
    # Step 1: Cypher retrieval
    discrepancies = get_discrepancies()

    # Step 2: Serialize
    context = serialize_discrepancies(discrepancies)

    # Step 3: LLM analysis
    response = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""{context}

Analyze these Knowledge Graph discrepancies and provide:
1. A severity ranking of the issues (Critical / Warning / Info)
2. For each RELATIONSHIP_CONFLICT: explain the clinical risk of having contradictory data
3. For MISSING_CLASS and ORPHANED_NODE: explain the data quality impact
4. Specific remediation recommendations for each issue type
5. An overall data quality score (0-100) with justification

Be specific and actionable."""
        }]
    )
    return response.content[0].text


def llm_symptom_lookup(symptom: str) -> str:
    """GraphRAG: fetch drugs for symptom → LLM comparison."""
    # Step 1: Cypher retrieval
    drugs = get_symptom_drugs(symptom)

    # Step 2: Serialize
    context = serialize_symptom_drugs(drugs, symptom)

    # Step 3: LLM analysis
    response = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""{context}

For the symptom '{symptom}', analyze the available treatment options:
1. Compare first-line vs second-line options based on drug class
2. Highlight OTC options suitable for self-treatment
3. Note any important considerations between the options
4. Suggest a logical treatment escalation path

Keep it practical and patient-friendly."""
        }]
    )
    return response.content[0].text


# ══════════════════════════════════════════════════════════════════════════════
# 4. FREE CHAT — natural language → auto Cypher → LLM
# ══════════════════════════════════════════════════════════════════════════════

def llm_free_chat(user_question: str) -> str:
    """
    GraphRAG free chat:
    1. LLM decides what to query
    2. We run Cypher
    3. LLM answers with graph context
    """
    # Step 1: Ask LLM to identify the drug/symptom from question
    intent = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"""Extract from this question the drug name OR symptom name to look up in a knowledge graph.
Reply with JSON only: {{"type": "drug"|"symptom"|"discrepancy", "value": "name or null"}}

Question: {user_question}"""
        }]
    )

    try:
        raw = intent.content[0].text.strip()
        # strip markdown if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        intent_type = parsed.get("type")
        intent_value = parsed.get("value")
    except Exception:
        intent_type = "unknown"
        intent_value = None

    # Step 2: Fetch relevant subgraph
    if intent_type == "drug" and intent_value:
        subgraph = get_drug_subgraph(intent_value)
        context = serialize_drug_subgraph(subgraph)
    elif intent_type == "symptom" and intent_value:
        drugs = get_symptom_drugs(intent_value)
        context = serialize_symptom_drugs(drugs, intent_value)
    elif intent_type == "discrepancy":
        discrepancies = get_discrepancies()
        context = serialize_discrepancies(discrepancies)
    else:
        context = "No specific drug or symptom identified. Answering from general knowledge."

    # Step 3: Answer with context
    response = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Knowledge Graph Context:
{context}

User Question: {user_question}

Answer the question using the knowledge graph data above as your primary source.
If the data doesn't contain the answer, say so clearly."""
        }]
    )
    return response.content[0].text


# ══════════════════════════════════════════════════════════════════════════════
# 5. MAIN — demo runner
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    print("\n" + "═" * 60)
    print("  MedCheck GraphRAG Pipeline")
    print("  Neo4j KG + Claude (Anthropic)")
    print("═" * 60)

    # ── Demo 1: Drug analysis
    print("\n[1] DRUG ANALYSIS — BPC-157")
    print("-" * 40)
    print(llm_analyze_drug("BPC-157"))

    # ── Demo 2: Discrepancy audit
    print("\n[2] DISCREPANCY AUDIT")
    print("-" * 40)
    print(llm_analyze_discrepancies())

    # ── Demo 3: Symptom lookup
    print("\n[3] SYMPTOM LOOKUP — Pain")
    print("-" * 40)
    print(llm_symptom_lookup("Pain"))

    # ── Demo 4: Free chat
    print("\n[4] FREE CHAT")
    print("-" * 40)
    questions = [
        "Is it safe to combine BPC-157 with Warfarin?",
        "What are the data quality issues in this knowledge graph?",
        "What can I take for a fever?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print(f"A: {llm_free_chat(q)}")
        print()

    driver.close()
    print("\n✅ GraphRAG pipeline complete.")
