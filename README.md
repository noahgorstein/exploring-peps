# Exploring Python Enhancement Proposals (PEPs) with Python and Graphs

This is the code that accompanies by blog post on [Exploring Python Enhancement Proposals (PEPs) with Python and Graphs](https://noahgorstein.com/blog/exploring-peps-with-python-and-graphs). 

The code in this repository is used to generate the data visualizations in the blog post.

## Installation

To install, use [`uv`](https://docs.astral.sh/uv/getting-started/installation/) to install the dependencies and run the code:

```bash
uv run src/main.py
```

You should see output like the following:

```bash
Converting PEPs to RDF...
RDF data saved to generated/
Generating visualizations...
Generating visualization for pep_supersession.html...
Generating visualization for pep_482_authors_contributions.html...
Generating visualization for pep_dependencies.html...
Generating visualization for pep_status_pie_chart.html...
Generating visualization for guidos_peps_over_time.html...
Visualizations saved to generated/visualizations/
```

The generated visualizations and RDF will be saved in the `generated` directory.
- The RDF schema is saved as [`schema.ttl`](./generated/schema.ttl) and the instance RDF data is saved as [`data.ttl`](./generated/data.ttl). These are included in the repository if you want to view or use them without running the code.
- The graph visualizations are saved as HTML in the `generated/visualizations` directory. These are not included in the repository, but you can view them in the blog post.
