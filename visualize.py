import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from neo4j import GraphDatabase

URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "Ad4m+5amo12_Ad4m+5amo12"  # zmeň na svoje

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def get_top_drugs(limit=15):
    with driver.session() as session:
        result = session.run("""
            MATCH (d:Drug)-[r:INTERACTS_WITH]-()
            RETURN coalesce(d.display_name, d.name) AS drug, count(r) AS interactions
            ORDER BY interactions DESC
            LIMIT $limit
        """, limit=limit)
        return [(r["drug"], r["interactions"]) for r in result]

def get_risk_distribution():
    with driver.session() as session:
        result = session.run("""
            MATCH ()-[r:INTERACTS_WITH]->()
            WHERE r.risk IS NOT NULL
            RETURN r.risk AS risk, count(r) AS total
            ORDER BY total DESC
        """)
        return [(r["risk"], r["total"]) for r in result]

def get_category_interactions():
    with driver.session() as session:
        result = session.run("""
            MATCH (d:Drug)-[:BELONGS_TO]->(c:Category)
            MATCH (d)-[r:INTERACTS_WITH|CONTRAINDICATED_WITH]->()
            RETURN c.name AS category, count(r) AS interactions
            ORDER BY interactions DESC
        """)
        return [(r["category"], r["interactions"]) for r in result]

def plot_all():
    fig, axes = plt.subplots(1, 3, figsize=(20, 7))
    fig.suptitle('MedCheck — Drug Interaction Analysis', fontsize=16, fontweight='bold', y=1.02)

    # Graf 1 – Top 15 liekov podla interakcii
    drugs, counts = zip(*get_top_drugs(15))
    colors = ['#c0392b' if c > 400 else '#e67e22' if c > 350 else '#2a52be' for c in counts]
    bars = axes[0].barh(drugs, counts, color=colors)
    axes[0].set_title('Top 15 Drugs by Interactions', fontweight='bold')
    axes[0].set_xlabel('Number of Interactions')
    axes[0].invert_yaxis()
    for bar, count in zip(bars, counts):
        axes[0].text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
                    str(count), va='center', fontsize=9)

    # Graf 2 – Risk distribution
    risk_data = get_risk_distribution()
    if risk_data:
        risks, totals = zip(*risk_data)
        risk_colors = {'HIGH': '#c0392b', 'MEDIUM': '#e67e22', 'LOW': '#2ecc71'}
        pie_colors = [risk_colors.get(r, '#95a5a6') for r in risks]
        axes[1].pie(totals, labels=risks, colors=pie_colors,
                   autopct='%1.1f%%', startangle=90)
        axes[1].set_title('Interaction Risk Distribution', fontweight='bold')
    else:
        axes[1].text(0.5, 0.5, 'No risk data\navailable',
                    ha='center', va='center', transform=axes[1].transAxes)
        axes[1].set_title('Interaction Risk Distribution', fontweight='bold')

    # Graf 3 – Interakcie podla kategorie
    cat_data = get_category_interactions()
    if cat_data:
        cats, cat_counts = zip(*cat_data)
        cat_colors = ['#2a52be', '#1a3a9e', '#4a90d9', '#6baed6',
                     '#2171b5', '#084594', '#c6dbef', '#deebf7'][:len(cats)]
        axes[2].bar(cats, cat_counts, color=cat_colors)
        axes[2].set_title('Interactions by Drug Category', fontweight='bold')
        axes[2].set_xlabel('Category')
        axes[2].set_ylabel('Interactions')
        axes[2].tick_params(axis='x', rotation=35)
    else:
        axes[2].text(0.5, 0.5, 'No category data\navailable',
                    ha='center', va='center', transform=axes[2].transAxes)
        axes[2].set_title('Interactions by Category', fontweight='bold')

    plt.tight_layout()
    plt.savefig('medcheck_analysis.png', dpi=150, bbox_inches='tight')
    print("Saved: medcheck_analysis.png")
    plt.show()

if __name__ == "__main__":
    plot_all()