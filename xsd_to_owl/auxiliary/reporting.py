import rdflib


def add_ontology_statistics(graph, base_uri, source_file=None, uri_encode_method=None):
    """
    Add statistics about the transformed ontology as an rdfs:comment annotation.

    Args:
        graph (rdflib.Graph): The RDF graph containing the ontology
        base_uri (str): The base URI of the ontology
        source_file (str, optional): Name of the source XSD file
        uri_encode_method (str, optional): The URI encoding method used
    """
    # Count types of resources
    classes = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Class)))
    datatype_props = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty)))
    object_props = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty)))
    concept_schemes = len(list(graph.subjects(rdflib.RDF.type, rdflib.SKOS.ConceptScheme)))
    concepts = len(list(graph.subjects(rdflib.RDF.type, rdflib.SKOS.Concept)))

    # Create the ontology URI
    ontology_uri = rdflib.URIRef(base_uri)

    # Create or find the ontology declaration
    if (ontology_uri, rdflib.RDF.type, rdflib.OWL.Ontology) not in graph:
        graph.add((ontology_uri, rdflib.RDF.type, rdflib.OWL.Ontology))

    # Build statistics string
    stats_comment = f"""Ontology statistics:
- Total triples: {len(graph)}
- OWL Classes: {classes}
- Datatype Properties: {datatype_props}
- Object Properties: {object_props}
- SKOS Concept Schemes: {concept_schemes}
- SKOS Concepts: {concepts}
"""

    # Add optional information if provided
    if uri_encode_method:
        stats_comment += f"- URI encoding method: {uri_encode_method}\n"
    if source_file:
        stats_comment += f"- Source XSD: {source_file}\n"

    # Add the statistics as a comment to the ontology
    graph.add((ontology_uri, rdflib.RDFS.comment, rdflib.Literal(stats_comment)))

    return graph


def print_ontology_statistics(graph):
    """
    Print statistics about the ontology to the console.

    Args:
        graph (rdflib.Graph): The RDF graph containing the ontology
    """
    # Count types of resources
    classes = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Class)))
    datatype_props = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty)))
    object_props = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty)))
    concept_schemes = len(list(graph.subjects(rdflib.RDF.type, rdflib.SKOS.ConceptScheme)))
    concepts = len(list(graph.subjects(rdflib.RDF.type, rdflib.SKOS.Concept)))

    # Print the statistics
    print("\n--- Ontology Statistics ---")
    print(f"Total triples: {len(graph)}")
    print(f"OWL Classes: {classes}")
    print(f"Datatype Properties: {datatype_props}")
    print(f"Object Properties: {object_props}")
    print(f"SKOS Concept Schemes: {concept_schemes}")
    print(f"SKOS Concepts: {concepts}")
    print("-------------------------")

