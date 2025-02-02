import json
import re
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, OWL, XSD, URIRef
from datetime import datetime
import urllib
import requests
from pathlib import Path


SCHEMA_NS = Namespace("https://noahgorstein.com/peps/schema/")
DEFAULT_NS = Namespace("https://python.org/peps/")

BACKTICK_HYPERLINK_REGEX = (
    r"`(\d{2}-\w{3}-\d{4}) <([^>]+)>`__"  # Matches Sphinx RST backtick hyperlinks
)
DATE_ONLY_REGEX = r"(\d{2}-\w{3}-\d{4})"  # Matches dates in dd-MMM-yyyy format
URL_REGEX = r"https?://\S+"  # Matches standard URLs


def parse_sphinx_resolution(resolution: str) -> dict[str, str] | None:
    """
    Parse a Sphinx RST-style resolution string for dates and URLs.
    """
    if match := re.match(BACKTICK_HYPERLINK_REGEX, resolution):
        return {"date": match.group(1), "url": match.group(2)}

    if re.match(URL_REGEX, resolution):
        return {"url": resolution}

    return None


def parse_sphinx_post_history(post_history: str) -> list[dict[str, str]]:
    """
    Parse a Sphinx RST-style post history string for dates and URLs.
    """
    matches = re.findall(BACKTICK_HYPERLINK_REGEX, post_history)
    if matches:
        return [{"date": date, "url": url} for date, url in matches]

    matches = re.findall(DATE_ONLY_REGEX, post_history)
    return [{"date": date} for date in matches]


def define_classes(schema_graph: Graph, schema_namespace: Namespace):
    """
    Define classes for the PEP schema.
    """
    schema_graph.add((schema_namespace.PythonEnhancementProposal, RDF.type, OWL.Class))
    schema_graph.add(
        (
            schema_namespace.PythonEnhancementProposal,
            RDFS.label,
            Literal("Python Enhancement Proposal"),
        )
    )

    schema_graph.add((schema_namespace.Author, RDF.type, OWL.Class))
    schema_graph.add((schema_namespace.Author, RDFS.label, Literal("PEP Author")))

    schema_graph.add((schema_namespace.Resolution, RDF.type, OWL.Class))
    schema_graph.add(
        (schema_namespace.Resolution, RDFS.label, Literal("PEP Resolution"))
    )

    schema_graph.add((schema_namespace.Post, RDF.type, OWL.Class))
    schema_graph.add((schema_namespace.Post, RDFS.label, Literal("PEP Post")))


def define_properties(schema_graph: Graph, schema_namespace: Namespace):
    """
    Define properties for the PEP schema.
    """
    property_definitions = [
        (
            schema_namespace.id,
            "id of the PEP",
            "the identifier of the PEP.",
            schema_namespace.PythonEnhancementProposal,
            XSD.int,
        ),
        (
            schema_namespace.url,
            "URL of the PEP",
            "the URL of the PEP.",
            schema_namespace.PythonEnhancementProposal,
            XSD.anyURI,
        ),
        (
            schema_namespace.title,
            "title of the PEP",
            "the title of the PEP.",
            schema_namespace.PythonEnhancementProposal,
            XSD.string,
        ),
        (
            schema_namespace.hasAuthor,
            "author of the PEP",
            "An author of the PEP.",
            schema_namespace.PythonEnhancementProposal,
            schema_namespace.Author,
        ),
        (
            schema_namespace.dateCreated,
            "creation date",
            "The date the PEP was created",
            schema_namespace.PythonEnhancementProposal,
            XSD.date,
        ),
        (
            schema_namespace.status,
            "PEP status",
            "The current status of the PEP",
            schema_namespace.PythonEnhancementProposal,
            XSD.string,
        ),
        (
            schema_namespace.type,
            "PEP type",
            "The type of the PEP",
            schema_namespace.PythonEnhancementProposal,
            XSD.string,
        ),
        (
            schema_namespace.pythonVersion,
            "Python version",
            "The Python version this PEP is targeted for",
            schema_namespace.PythonEnhancementProposal,
            XSD.string,
        ),
        (
            schema_namespace.requires,
            "requires PEP",
            "Other PEPs that this PEP depends on",
            schema_namespace.PythonEnhancementProposal,
            schema_namespace.PythonEnhancementProposal,
        ),
        (
            schema_namespace.replaces,
            "replaces PEP",
            "The PEP that this PEP replaces",
            schema_namespace.PythonEnhancementProposal,
            schema_namespace.PythonEnhancementProposal,
        ),
        (
            schema_namespace.supersededBy,
            "superseded by PEP",
            "The PEP that supersedes this PEP",
            schema_namespace.PythonEnhancementProposal,
            schema_namespace.PythonEnhancementProposal,
        ),
        (
            schema_namespace.discussionsTo,
            "discussions to",
            "The mailing list or URL where the PEP is being discussed",
            schema_namespace.PythonEnhancementProposal,
            XSD.string,
        ),
        (
            schema_namespace.topic,
            "topic",
            "The topic area of the PEP",
            schema_namespace.PythonEnhancementProposal,
            XSD.string,
        ),
        (
            schema_namespace.hasResolution,
            "has a resolution",
            "Resolution for this PEP",
            schema_namespace.PythonEnhancementProposal,
            schema_namespace.Resolution,
        ),
        (
            schema_namespace.hasPost,
            "has post associated with PEP",
            "History of significant posts related to the PEP",
            schema_namespace.PythonEnhancementProposal,
            schema_namespace.Post,
        ),
        (
            schema_namespace.resolutionUrl,
            "resolution URL",
            "The URL of the resolution",
            schema_namespace.Resolution,
            XSD.anyURI,
        ),
        (
            schema_namespace.resolutionDate,
            "resolution date",
            "The date of the resolution",
            schema_namespace.Resolution,
            XSD.date,
        ),
        (
            schema_namespace.postUrl,
            "post URL",
            "The URL of the post",
            schema_namespace.Post,
            XSD.anyURI,
        ),
        (
            schema_namespace.postDate,
            "post date",
            "The date of the post",
            schema_namespace.Post,
            XSD.date,
        ),
    ]

    for prop, label, comment, domain, rng in property_definitions:
        if isinstance(rng, URIRef) and rng.startswith(str(XSD)):
            schema_graph.add((prop, RDF.type, OWL.DatatypeProperty))
        else:
            schema_graph.add((prop, RDF.type, OWL.ObjectProperty))

        schema_graph.add((prop, RDFS.label, Literal(label)))
        schema_graph.add((prop, RDFS.comment, Literal(comment)))
        schema_graph.add((prop, RDFS.domain, domain))
        schema_graph.add((prop, RDFS.range, rng))


def create_instance_data(
    json_data: dict,
    instance_data_graph: Graph,
    schema_namespace: Namespace,
    instance_namespace: Namespace,
):
    """
    Create instance data for PEPs in the RDF graph.
    """
    for _, pep_data in json_data.items():
        pep_uri = instance_namespace[f"pep-{str(pep_data['number'])}"]

        instance_data_graph.add(
            (pep_uri, RDF.type, schema_namespace.PythonEnhancementProposal)
        )
        instance_data_graph.add((pep_uri, RDFS.label, Literal(pep_data["title"])))
        instance_data_graph.add(
            (pep_uri, schema_namespace.title, Literal(pep_data["title"]))
        )
        instance_data_graph.add(
            (
                pep_uri,
                schema_namespace.id,
                Literal(pep_data["number"], datatype=XSD.int),
            )
        )
        instance_data_graph.add(
            (
                pep_uri,
                schema_namespace.url,
                Literal(pep_data["url"], datatype=XSD.anyURI),
            )
        )
        instance_data_graph.add(
            (pep_uri, schema_namespace.status, Literal(pep_data["status"]))
        )
        instance_data_graph.add(
            (
                pep_uri,
                schema_namespace.pythonVersion,
                Literal(pep_data["python_version"]),
            )
        )
        instance_data_graph.add(
            (pep_uri, schema_namespace.type, Literal(pep_data["type"]))
        )

        if pep_data.get("authors"):
            for author in pep_data["authors"].split(", "):
                author_uri = instance_namespace[
                    f"author/{urllib.parse.quote_plus(author)}"
                ]
                instance_data_graph.add(
                    (pep_uri, schema_namespace.hasAuthor, author_uri)
                )
                instance_data_graph.add((author_uri, RDF.type, schema_namespace.Author))
                instance_data_graph.add((author_uri, RDFS.label, Literal(author)))

        if pep_data.get("topic"):
            topics = [topic.strip() for topic in pep_data["topic"].split(",")]
            for topic in topics:
                instance_data_graph.add(
                    (pep_uri, schema_namespace.topic, Literal(topic))
                )

        if pep_data.get("created"):
            created_date = datetime.strptime(pep_data["created"], "%d-%b-%Y")
            instance_data_graph.add(
                (
                    pep_uri,
                    schema_namespace.dateCreated,
                    Literal(created_date.isoformat(), datatype=XSD.date),
                )
            )

        if pep_data.get("superseded_by"):
            instance_data_graph.add(
                (
                    pep_uri,
                    schema_namespace.supersededBy,
                    instance_namespace[f"pep-{str(pep_data['superseded_by'])}"],
                ),
            )

        if pep_data.get("replaces"):
            replaced_peps = [pep.strip() for pep in pep_data["replaces"].split(",")]
            for pep in replaced_peps:
                instance_data_graph.add(
                    (
                        pep_uri,
                        schema_namespace.replaces,
                        instance_namespace[f"pep-{str(pep)}"],
                    )
                )

        if pep_data.get("requires"):
            required_peps = [pep.strip() for pep in pep_data["requires"].split(",")]
            for pep in required_peps:
                instance_data_graph.add(
                    (
                        pep_uri,
                        schema_namespace.requires,
                        instance_namespace[f"pep-{str(pep)}"],
                    )
                )

        if pep_data.get("discussions_to"):
            instance_data_graph.add(
                (
                    pep_uri,
                    schema_namespace.discussionsTo,
                    Literal(pep_data.get("discussions_to")),
                )
            )

        if pep_data.get("resolution"):
            resolution_data = parse_sphinx_resolution(pep_data["resolution"])
            if resolution_data:
                resolution_node = BNode()
                instance_data_graph.add(
                    (pep_uri, schema_namespace.hasResolution, resolution_node)
                )
                instance_data_graph.add(
                    (resolution_node, RDF.type, schema_namespace.Resolution)
                )

                if "url" in resolution_data:
                    instance_data_graph.add(
                        (
                            resolution_node,
                            schema_namespace.resolutionUrl,
                            Literal(resolution_data["url"], datatype=XSD.anyURI),
                        )
                    )

                if "date" in resolution_data:
                    resolution_date = datetime.strptime(
                        resolution_data["date"], "%d-%b-%Y"
                    )
                    instance_data_graph.add(
                        (
                            resolution_node,
                            schema_namespace.resolutionDate,
                            Literal(resolution_date.isoformat(), datatype=XSD.date),
                        )
                    )

        if pep_data.get("post_history"):
            post_history_data = parse_sphinx_post_history(pep_data["post_history"])
            for post in post_history_data:
                post_node = BNode()
                instance_data_graph.add((pep_uri, schema_namespace.hasPost, post_node))
                instance_data_graph.add((post_node, RDF.type, schema_namespace.Post))
                post_date = datetime.strptime(post["date"], "%d-%b-%Y")
                instance_data_graph.add(
                    (
                        post_node,
                        schema_namespace.postDate,
                        Literal(post_date.isoformat(), datatype=XSD.date),
                    )
                )
                if "url" in post:
                    instance_data_graph.add(
                        (
                            post_node,
                            schema_namespace.postUrl,
                            Literal(post["url"], datatype=XSD.anyURI),
                        )
                    )


def fetch_pep_data() -> dict:
    """
    Fetch PEP data from the PEPs API and cache it in a local file.
    """
    pep_data_filename = "pep-data.json"
    pep_data_file = Path(f"./{pep_data_filename}")
    if not pep_data_file.exists():
        data = requests.get("https://peps.python.org/api/peps.json").json()
        with pep_data_file.open("w") as f:
            json.dump(data, f)
        return data
    with pep_data_file.open() as f:
        return json.load(f)


def convert_peps_to_rdf() -> tuple[Graph, Graph]:
    """
    Convert PEP data to RDF graphs.
    """
    pep_data = fetch_pep_data()

    schema_graph = Graph()
    instance_data_graph = Graph()

    for g in [schema_graph, instance_data_graph]:
        g.bind("peps", SCHEMA_NS)
        g.bind("", DEFAULT_NS)

    define_classes(schema_graph, SCHEMA_NS)
    define_properties(schema_graph, SCHEMA_NS)

    create_instance_data(pep_data, instance_data_graph, SCHEMA_NS, DEFAULT_NS)

    return schema_graph, instance_data_graph
