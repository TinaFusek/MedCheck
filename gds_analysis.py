from neo4j import GraphDatabase
import matplotlib.pyplot as plt
import numpy as np

URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "..."  # zmeň na svoje

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def setup_projection():
    with driver.session() as session:
        session.run("CALL gds.graph.drop('drugGraph', false)")
        session.run("""
            CALL gds.graph.project(
                'drugGraph',
                'Drug',
                'INTERACTS_WITH'
            )
        """)
        print("Graph projection created: drugGraph")

def run_pagerank():
    with driver.session() as session:
        result = session.run("""
            CALL gds.pageRank.stream('drugGraph')
            YIELD nodeId, score
            RETURN coalesce(
                gds.util.asNode(nodeId).display_name,
                gds.util.asNode(nodeId).name
            ) AS drug, score
            ORDER BY score DESC
            LIMIT 15
        """)
        return [(r["drug"], round(r["score"], 4)) for r in result]

def run_betweenness():
    with driver.session() as session:
        result = session.run("""
            CALL gds.betweenness.stream('drugGraph')
            YIELD nodeId, score
            RETURN coalesce(
                gds.util.asNode(nodeId).display_name,
                gds.util.asNode(nodeId).name
            ) AS drug, score
            ORDER BY score DESC
            LIMIT 15
        """)
        return [(r["drug"], round(r["score"], 2)) for r in result]

def run_community():
    with driver.session() as session:
        result = session.run("""
            CALL gds.louvain.stream('drugGraph')
            YIELD nodeId, communityId
            RETURN communityId, count(nodeId) AS size
            ORDER BY size DESC
            LIMIT 10
        """)
        return [(r["communityId"], r["size"]) for r in result]

def plot_gds(pagerank, betweenness, communities):
    fig, axes = plt.subplots(1, 3, figsize=(22, 7))
    fig.suptitle('MedCheck — Graph Data Science Analysis (GDS)', fontsize=16, fontweight='bold')

    # PageRank
    drugs_pr, scores_pr = zip(*pagerank)
    colors_pr = ['#c0392b' if s > 1.5 else '#e67e22' if s > 1.0 else '#2a52be' for s in scores_pr]
    axes[0].barh(drugs_pr, scores_pr, color=colors_pr)
    axes[0].set_title('PageRank — Most Influential Drugs', fontweight='bold')
    axes[0].set_xlabel('PageRank Score')
    axes[0].invert_yaxis()

    # Betweenness
    drugs_bt, scores_bt = zip(*betweenness)
    axes[1].barh(drugs_bt, scores_bt, color='#2a52be')
    axes[1].set_title('Betweenness Centrality\n(Bridge Drugs)', fontweight='bold')
    axes[1].set_xlabel('Betweenness Score')
    axes[1].invert_yaxis()

    # Communities
    comm_ids, comm_sizes = zip(*communities)
    axes[2].bar([f"C{i}" for i in comm_ids], comm_sizes, color='#4a90d9')
    axes[2].set_title('Drug Communities (Louvain)', fontweight='bold')
    axes[2].set_xlabel('Community')
    axes[2].set_ylabel('Number of Drugs')

    plt.tight_layout()
    plt.savefig('gds_analysis.png', dpi=150, bbox_inches='tight')
    print("Saved: gds_analysis.png")
    plt.show()

if __name__ == "__main__":
    print("Setting up graph projection...")
    setup_projection()

    print("\nRunning PageRank...")
    pr = run_pagerank()
    print(f"Top drug: {pr[0][0]} (score: {pr[0][1]})")

    print("\nRunning Betweenness Centrality...")
    bt = run_betweenness()
    print(f"Top bridge drug: {bt[0][0]} (score: {bt[0][1]})")

    print("\nRunning Community Detection (Louvain)...")
    cm = run_community()
    print(f"Found {len(cm)} major communities")

    print("\nGenerating plots...")
    plot_gds(pr, bt, cm)
