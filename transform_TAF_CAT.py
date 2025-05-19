import os
import sys
import rdflib
import argparse
from typing import List, Union, Optional

from xsd_to_owl import create_taf_cat_transformer
from xsd_to_owl.utils import logging


def taf_cat_transformation(
    xsd_paths: Union[str, List[str]],
    base_uri: str = "http://example.org/ontology#",
    uri_encode_method: str = "underscore",
    output_path: Optional[str] = None,
    output_format: str = "turtle",
    log_level: str = "info"
) -> Union[rdflib.Graph, bool]:
    """
    Transform TAF CAT XSD file(s) to OWL/SKOS ontology.
    
    Args:
        xsd_paths: Path to a single XSD file or a list of XSD file paths
        base_uri: Base URI for the ontology
        uri_encode_method: Method to encode URIs with spaces
        output_path: Path to save the output file (if None, will use default path)
        output_format: Output_owl format (turtle, xml, n3, json-ld, etc.)
        log_level: Logging level (debug, info, warning, error)
        
    Returns:
        rdflib.Graph if successful, False otherwise
    """
    # Set up logging
    _setup_logging(log_level)
    
    # Create a transformer with enhanced rules
    transformer = create_taf_cat_transformer(uri_encode_method)
    
    # Convert single path to list for consistent processing
    if isinstance(xsd_paths, str):
        xsd_paths = [xsd_paths]
    
    # Validate all paths exist before processing
    for path in xsd_paths:
        abs_path = os.path.abspath(path)
        logging.info(f"Validating XSD file: {abs_path}")
        if not os.path.exists(abs_path):
            logging.error(f"XSD file not found at path: {abs_path}")
            return False
    
    # Create a merged graph for all XSD files
    merged_graph = rdflib.Graph()
    
    # Process each XSD file
    for xsd_path in xsd_paths:
        try:
            logging.info(f"Processing XSD file: {xsd_path}")
            graph = transformer.transform(xsd_path, base_uri, uri_encode_method)
            
            # Merge with the combined graph
            if len(xsd_paths) > 1:
                logging.info(f"Merging graph from {xsd_path} (triples: {len(graph)})")
                for triple in graph:
                    merged_graph.add(triple)
            else:
                merged_graph = graph
                
        except Exception as e:
            logging.error(f"Error transforming {xsd_path}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    # Post-process the graph to fix inconsistent property types
    logging.info("Post-processing graph to fix inconsistent property types...")
    post_process_graph(merged_graph)
    
    # Apply ontology annotations
    logging.info("Applying ontology annotations...")
    apply_ontology_annotations(merged_graph, xsd_paths[0])
    
    # Print statistics for the final merged graph
    logging.info(f"Transformation successful!")
    logging.info(f"Number of triples in final graph: {len(merged_graph)}")
    
    # Count types of resources
    classes = len(list(merged_graph.subjects(rdflib.RDF.type, rdflib.OWL.Class)))
    datatype_props = len(list(merged_graph.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty)))
    object_props = len(list(merged_graph.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty)))
    concept_schemes = len(list(merged_graph.subjects(rdflib.RDF.type, rdflib.SKOS.ConceptScheme)))
    concepts = len(list(merged_graph.subjects(rdflib.RDF.type, rdflib.SKOS.Concept)))
    
    stats = {
        "classes": classes,
        "datatype_properties": datatype_props,
        "object_properties": object_props,
        "concept_schemes": concept_schemes,
        "concepts": concepts,
        "total_triples": len(merged_graph)
    }
    
    logging.info(f"OWL Classes: {classes}")
    logging.info(f"Datatype Properties: {datatype_props}")
    logging.info(f"Object Properties: {object_props}")
    logging.info(f"SKOS Concept Schemes: {concept_schemes}")
    logging.info(f"SKOS Concepts: {concepts}")
    
    # Determine output path
    if output_path is None:
        # Create Output_owl directory if it doesn't exist
        os.makedirs("Output_owl", exist_ok=True)
        
        # Default output path based on input files
        if len(xsd_paths) == 1:
            base_name = os.path.splitext(os.path.basename(xsd_paths[0]))[0]
            output_path = f"Output_owl/output_{base_name}_ontology.{_get_file_extension(output_format)}"
        else:
            output_path = f"Output_owl/merged_taf_cat_ontology.{_get_file_extension(output_format)}"
    
    # Serialize to the specified format
    try:
        # Save to file using transformer's save method
        transformer.save(merged_graph, output_path, output_format)
        
        # Get a sample for display
        serialized = merged_graph.serialize(format=output_format)
        sample = serialized[:1000] + "..." if len(serialized) > 1000 else serialized
        logging.info(f"Sample of the generated ontology (in {output_format} format):")
        print(sample)  # Print directly for better readability
        
        logging.info(f"Full ontology saved to {output_path}")
        
        return merged_graph
    except Exception as e:
        logging.error(f"Error serializing graph: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False


def _get_file_extension(format_name):
    """Get the appropriate file extension for the output format"""
    format_extensions = {
        "turtle": "ttl",
        "xml": "rdf",
        "n3": "n3",
        "nt": "nt",
        "json-ld": "jsonld",
        "nquads": "nq",
        "trig": "trig"
    }
    return format_extensions.get(format_name.lower(), "ttl")


def _setup_logging(level_name):
    """Set up logging with the specified level"""
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }
    level = level_map.get(level_name.lower(), logging.INFO)
    logging.set_level(level)


def apply_ontology_annotations(graph, xsd_path):
    """
    Apply ontology annotations to the graph.
    
    This function adds metadata such as title, description, and statistics to the ontology.
    
    Args:
        graph: The RDF graph to annotate
        xsd_path: Path to the XSD file used to generate the ontology
    """
    # Find the ontology IRI
    ontology_iris = list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
    if not ontology_iris:
        logging.warning("No ontology IRI found, cannot add annotations")
        return
    
    ontology_iri = ontology_iris[0]
    logging.info(f"Adding annotations to ontology IRI: {ontology_iri}")
    
    # Add basic annotations
    graph.add((ontology_iri, rdflib.RDFS.label, rdflib.Literal(f"TAF CAT Ontology")))
    graph.add((ontology_iri, rdflib.RDFS.comment, rdflib.Literal(f"Ontology generated from XSD schema {xsd_path} using xsd_to_owl transformation framework")))
    
    # Count types of resources
    classes = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Class)))
    datatype_props = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty)))
    object_props = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty)))
    concept_schemes = len(list(graph.subjects(rdflib.RDF.type, rdflib.SKOS.ConceptScheme)))
    concepts = len(list(graph.subjects(rdflib.RDF.type, rdflib.SKOS.Concept)))
    
    # Add statistics as a single annotation
    stats_text = (f"Statistics: Total triples: {len(graph)}, OWL Classes: {classes}, "
                 f"Datatype Properties: {datatype_props}, Object Properties: {object_props}, "
                 f"SKOS Concept Schemes: {concept_schemes}, SKOS Concepts: {concepts}")
    graph.add((ontology_iri, rdflib.RDFS.comment, rdflib.Literal(stats_text)))
    
    # Add licensing information
    graph.add((ontology_iri, rdflib.URIRef("http://purl.org/dc/terms/license"), rdflib.Literal("restricted - no license")))
    
    logging.info("Ontology annotations added successfully")


def post_process_graph(graph):
    """
    Post-process the graph to fix inconsistent property types.
    
    This function looks for properties that are both datatype and object properties,
    and fixes them based on the special cases configuration and property types.
    It also fixes properties with multiple XSD ranges.
    
    Args:
        graph: The RDF graph to process
    """
    import re
    import collections
    # Import special cases configuration
    from xsd_to_owl.config.special_cases import NEVER_OBJECT_PROPERTIES
    
    # Create a lowercase version of NEVER_OBJECT_PROPERTIES for case-insensitive matching
    never_object_properties_lower = {name.lower() for name in NEVER_OBJECT_PROPERTIES}
    
    # Find properties that are both datatype and object properties
    problematic_properties = []
    for s in graph.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        if (s, rdflib.RDF.type, rdflib.OWL.ObjectProperty) in graph:
            problematic_properties.append(s)
    
    # Find properties with multiple XSD ranges
    properties_with_multiple_ranges = []
    for s in graph.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty):
        # Get all XSD ranges for this property
        xsd_ranges = []
        for _, _, range_o in graph.triples((s, rdflib.RDFS.range, None)):
            if str(range_o).startswith(str(rdflib.XSD)):
                xsd_ranges.append(range_o)
        
        # If there are multiple XSD ranges, add to the list
        if len(xsd_ranges) > 1:
            properties_with_multiple_ranges.append((s, xsd_ranges))
    
    # Process properties with multiple XSD ranges
    if properties_with_multiple_ranges:
        logging.info(f"Found {len(properties_with_multiple_ranges)} properties with multiple XSD ranges")
        
        for s, ranges in properties_with_multiple_ranges:
            # Get property name
            property_name = None
            for _, _, label_o in graph.triples((s, rdflib.RDFS.label, None)):
                property_name = str(label_o)
                break
            
            if not property_name:
                continue
                
            logging.info(f"  Property {property_name} has multiple XSD ranges: {', '.join(str(r) for r in ranges)}")
            
            # Keep only xsd:string if both xsd:string and xsd:token are present
            if rdflib.XSD.string in ranges and rdflib.XSD.token in ranges:
                logging.info(f"  Removing xsd:token range from {property_name} (keeping xsd:string)")
                graph.remove((s, rdflib.RDFS.range, rdflib.XSD.token))
    
    # Process properties with inconsistent types
    if not problematic_properties:
        logging.info("No properties with inconsistent types found")
    else:
        logging.info(f"Found {len(problematic_properties)} properties with inconsistent types")
    
    for s in problematic_properties:
        # Get property name
        property_name = None
        for _, _, label_o in graph.triples((s, rdflib.RDFS.label, None)):
            property_name = str(label_o)
            break
        
        if not property_name:
            continue
        
        logging.info(f"  Property {property_name} is both a datatype and object property")
        
        # Check if it's in the special cases (case-insensitive)
        should_remove_object_property = property_name.lower() in never_object_properties_lower
        
        # Check if it has a comment indicating it's a Numeric type
        has_numeric_type = False
        for _, _, comment_o in graph.triples((s, rdflib.RDFS.comment, None)):
            comment = str(comment_o)
            if "Original XSD type was Numeric" in comment or re.search(r'Original XSD type was Numeric\d+(-\d+)?', comment):
                has_numeric_type = True
                break
        
        # Check if it has an XSD type range
        has_xsd_range = False
        for _, _, range_o in graph.triples((s, rdflib.RDFS.range, None)):
            if str(range_o).startswith(str(rdflib.XSD)):
                has_xsd_range = True
                break
        
        if should_remove_object_property or has_numeric_type or has_xsd_range:
            if has_numeric_type:
                logging.info(f"  {property_name} has a Numeric type, removing object property type")
            elif has_xsd_range:
                logging.info(f"  {property_name} has an XSD type range, removing object property type")
            else:
                logging.info(f"  {property_name} should never be an object property, removing object property type")
            
            # Remove object property type
            graph.remove((s, rdflib.RDF.type, rdflib.OWL.ObjectProperty))
            
            # Remove any object property ranges
            object_ranges = []
            for _, _, range_o in graph.triples((s, rdflib.RDFS.range, None)):
                if not str(range_o).startswith(str(rdflib.XSD)):
                    object_ranges.append(range_o)
            
            for range_o in object_ranges:
                graph.remove((s, rdflib.RDFS.range, range_o))
                logging.info(f"  Removed object range {range_o} from {property_name}")
        else:
            logging.info(f"  No special case handling for {property_name}, keeping both types")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Transform TAF CAT XSD to OWL')
    
    # Required arguments
    parser.add_argument('--xsd-path', type=str, action='append', required=True,
                        help='Path to the XSD file(s) (can be specified multiple times)')
    
    # Optional arguments
    parser.add_argument('--base-uri', type=str, default="http://example.org/ontology#",
                        help='Base URI for the ontology')
    parser.add_argument('--uri-encode', type=str, default="underscore",
                        choices=["percent", "underscore", "camelcase", "dash", "plus"],
                        help='Method to encode URIs with spaces')
    parser.add_argument('--output', type=str, default=None,
                        help='Path to save the output file')
    parser.add_argument('--format', type=str, default="turtle",
                        choices=["turtle", "xml", "n3", "nt", "json-ld", "nquads", "trig"],
                        help='Output_owl format')
    parser.add_argument('--log-level', type=str, default="info",
                        choices=["debug", "info", "warning", "error"],
                        help='Logging level')
    
    args = parser.parse_args()
    
    # Run the transformation
    taf_cat_transformation(
        args.xsd_path,
        args.base_uri,
        args.uri_encode,
        args.output,
        args.format,
        args.log_level
    )