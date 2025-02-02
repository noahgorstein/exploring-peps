import peps_to_rdf
from visualize import (
    generate_visualizations,
    visualize_guidos_peps,
    visualize_one_peps_authors_contributions,
    visualize_pep_dependencies,
    visualize_pep_status_distribution,
    visualize_pep_supersession,
)
from pathlib import Path


if __name__ == "__main__":
    generated_dir = Path("generated")
    generated_dir.mkdir(exist_ok=True)

    print("Converting PEPs to RDF...")
    schema_graph, data_graph = peps_to_rdf.convert_peps_to_rdf()

    schema_graph.serialize(f"{generated_dir}/schema.ttl", format="turtle")
    data_graph.serialize(f"{generated_dir}/data.ttl", format="turtle")
    print("RDF data saved to generated/")

    print("Generating visualizations...")
    generate_visualizations(
        data_graph,
        output_dir=f"{generated_dir}/visualizations/",
        visualizers={
            "pep_supersession.html": visualize_pep_supersession,
            "pep_482_authors_contributions.html": visualize_one_peps_authors_contributions,
            "pep_dependencies.html": visualize_pep_dependencies,
            "pep_status_pie_chart.html": visualize_pep_status_distribution,
            "guidos_peps_over_time.html": visualize_guidos_peps,
        },
    )
    print("Visualizations saved to generated/visualizations/")
