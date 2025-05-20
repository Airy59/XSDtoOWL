"""
Main converter module for XML to RDF transformation.
Provides the XMLtoRDFConverter class for orchestrating the transformation process.
"""

import os
from typing import Dict, List, Optional, Union, Any

import rdflib
from lxml import etree
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL

from xml_to_rdf.mapping import XMLtoRDFMapping
from xml_to_rdf.utils import xml_parsers
from xsd_to_owl.utils import logging


class XMLtoRDFConverter:
    """
    Main converter class for XML to RDF transformation.
    Uses the OWL ontology generated from the XSD schema to transform XML data to RDF.
    """
    
    def __init__(self, base_uri: str = "http://example.org/data#"):
        """
        Initialize a new converter.
        
        Args:
            base_uri: Base URI for the generated RDF data
        """
        self.base_uri = base_uri
        self.mapping = XMLtoRDFMapping()
        self.rules = []
        
        # Initialize namespaces
        self.ns = {
            'rdf': RDF,
            'rdfs': RDFS,
            'owl': OWL,
            'xsd': Namespace("http://www.w3.org/2001/XMLSchema#"),
            'base': Namespace(base_uri)
        }
        
        logging.debug(f"Initialized XML to RDF converter with base URI: {base_uri}")
    
    def register_rule(self, rule):
        """
        Register a transformation rule.
        
        Args:
            rule: A rule implementation
            
        Returns:
            self for chaining
        """
        self.rules.append(rule)
        logging.debug(f"Registered rule {rule.rule_id}")
        return self
    
    def convert(self, 
               xml_file: Union[str, bytes], 
               owl_ontology: Union[str, Graph],
               output_format: str = "turtle") -> Graph:
        """
        Convert XML data to RDF using the OWL ontology.
        
        Args:
            xml_file: Path to XML file or XML string/bytes
            owl_ontology: Path to OWL ontology file or rdflib.Graph
            output_format: Output format (turtle, xml, etc.)
            
        Returns:
            rdflib.Graph containing the RDF data
        """
        # Load the OWL ontology
        ontology_graph = self._load_ontology(owl_ontology)
        
        # Parse XML file or content
        xml_root = self._parse_xml(xml_file)
        
        # Create a new graph for the RDF data
        data_graph = Graph()
        
        # Add namespaces to the graph
        for prefix, namespace in self.ns.items():
            data_graph.bind(prefix, namespace)
        
        # Initialize the mapping with the ontology
        self.mapping.initialize(ontology_graph)
        
        # Process the XML root element
        self._process_element(xml_root, data_graph, None)
        
        # Log conversion completion
        logging.info(f"Conversion completed. Generated {len(data_graph)} triples.")
        
        return data_graph
    
    def _load_ontology(self, owl_ontology: Union[str, Graph]) -> Graph:
        """
        Load the OWL ontology.
        
        Args:
            owl_ontology: Path to OWL ontology file or rdflib.Graph
            
        Returns:
            rdflib.Graph containing the ontology
        """
        if isinstance(owl_ontology, Graph):
            return owl_ontology
        
        ontology_graph = Graph()
        try:
            ontology_graph.parse(owl_ontology, format=self._guess_format(owl_ontology))
            logging.info(f"Loaded ontology from {owl_ontology} with {len(ontology_graph)} triples")
        except Exception as e:
            logging.error(f"Failed to load ontology: {e}")
            raise
        
        return ontology_graph
    
    def _parse_xml(self, xml_file: Union[str, bytes]) -> etree._Element:
        """
        Parse XML file or content.
        
        Args:
            xml_file: Path to XML file or XML string/bytes
            
        Returns:
            lxml.etree._Element representing the XML root
        """
        return xml_parsers.parse_xml(xml_file)
    
    def _process_element(self, element: etree._Element, graph: Graph, parent_uri: Optional[URIRef]) -> Optional[URIRef]:
        """
        Process an XML element and add corresponding triples to the graph.
        
        Args:
            element: XML element to process
            graph: RDF graph to add triples to
            parent_uri: URI of the parent element (if any)
            
        Returns:
            URI of the processed element
        """
        # Get the element name (local name without namespace)
        element_name = xml_parsers.get_element_name(element)
        
        # Find the corresponding class in the ontology
        class_uri = self.mapping.get_class_uri(element_name)
        
        if class_uri:
            # Create a new instance of the class
            instance_uri = URIRef(f"{self.base_uri}{element_name}_{id(element)}")
            graph.add((instance_uri, RDF.type, class_uri))
            
            # If this element has a parent, link it to the parent
            if parent_uri:
                property_uri = self.mapping.get_property_uri(element_name)
                if property_uri:
                    graph.add((parent_uri, property_uri, instance_uri))
            
            # Process attributes
            attributes = xml_parsers.get_element_attributes(element)
            for attr_name, attr_value in attributes.items():
                self._process_attribute(attr_name, attr_value, instance_uri, graph)
            
            # Process child elements
            for child in element:
                self._process_element(child, graph, instance_uri)
            
            # If the element has text content and no children, add it as a property
            if xml_parsers.has_simple_content(element):
                # Check if there's a specific datatype property for the text content
                text_property = self.mapping.get_text_property_uri(element_name)
                if text_property:
                    # Try to determine the datatype
                    datatype = self.mapping.get_datatype(element_name)
                    if datatype:
                        typed_value = Literal(xml_parsers.get_element_text(element), datatype=datatype)
                        graph.add((instance_uri, text_property, typed_value))
                    else:
                        graph.add((instance_uri, text_property, Literal(xml_parsers.get_element_text(element))))
            
            return instance_uri
        
        # If no class is found, check if it's a simple property
        elif parent_uri:
            property_uri = self.mapping.get_property_uri(element_name)
            if property_uri:
                # If the element has text content, add it as a property value
                element_text = xml_parsers.get_element_text(element)
                if element_text:
                    # Try to determine the datatype
                    datatype = self.mapping.get_datatype(element_name)
                    if datatype:
                        typed_value = Literal(element_text, datatype=datatype)
                        graph.add((parent_uri, property_uri, typed_value))
                    else:
                        graph.add((parent_uri, property_uri, Literal(element_text)))
        
        return None
    
    def _process_attribute(self, attr_name: str, attr_value: str, subject_uri: URIRef, graph: Graph):
        """
        Process an XML attribute and add corresponding triples to the graph.
        
        Args:
            attr_name: Attribute name
            attr_value: Attribute value
            subject_uri: URI of the element that has this attribute
            graph: RDF graph to add triples to
        """
        # Find the corresponding property in the ontology
        property_uri = self.mapping.get_attribute_property_uri(attr_name)
        
        if property_uri:
            # Try to determine the datatype
            datatype = self.mapping.get_attribute_datatype(attr_name)
            if datatype:
                typed_value = Literal(attr_value, datatype=datatype)
                graph.add((subject_uri, property_uri, typed_value))
            else:
                graph.add((subject_uri, property_uri, Literal(attr_value)))
    
    def _guess_format(self, file_path: str) -> str:
        """
        Guess the RDF format based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Format string for rdflib
        """
        ext = os.path.splitext(file_path)[1].lower()
        format_map = {
            '.ttl': 'turtle',
            '.rdf': 'xml',
            '.owl': 'xml',
            '.n3': 'n3',
            '.nt': 'nt',
            '.jsonld': 'json-ld',
            '.nq': 'nquads',
            '.trig': 'trig'
        }
        return format_map.get(ext, 'turtle')
    
    def save(self, graph: Graph, output_file: str, format: str = "turtle") -> None:
        """
        Save the RDF graph to a file.
        
        Args:
            graph: rdflib.Graph to save
            output_file: Path to save the RDF data
            format: Output format (turtle, xml, etc.)
        """
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Serialize and save
        graph.serialize(destination=output_file, format=format)
        logging.info(f"Saved RDF data to {output_file} in {format} format")


def create_default_converter(base_uri: str = "http://example.org/data#") -> XMLtoRDFConverter:
    """
    Create a converter with default rules.
    
    Args:
        base_uri: Base URI for the generated RDF data
        
    Returns:
        A configured XMLtoRDFConverter
    """
    # Import rules here to avoid circular imports
    # from xml_to_rdf.rules.element_rules import ElementRule
    # from xml_to_rdf.rules.attribute_rules import AttributeRule
    # from xml_to_rdf.rules.value_rules import ValueRule
    
    # Create converter
    converter = XMLtoRDFConverter(base_uri)
    
    # Register rules
    # converter.register_rule(ElementRule())
    # converter.register_rule(AttributeRule())
    # converter.register_rule(ValueRule())
    
    return converter