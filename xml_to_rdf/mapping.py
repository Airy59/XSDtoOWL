"""
Mapping module for XML to RDF transformation.
Provides the XMLtoRDFMapping class for mapping XML elements to OWL classes and properties.
"""

from typing import Dict, Optional, Set, Tuple, Union

import rdflib
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL, XSD

from xsd_to_owl.utils import logging


class XMLtoRDFMapping:
    """
    Mapping class for XML to RDF transformation.
    Maps XML elements to OWL classes and properties based on the ontology.
    """
    
    def __init__(self):
        """
        Initialize a new mapping.
        """
        self.class_map = {}  # Maps element names to class URIs
        self.property_map = {}  # Maps element names to property URIs
        self.attribute_property_map = {}  # Maps attribute names to property URIs
        self.text_property_map = {}  # Maps element names to text content property URIs
        self.datatype_map = {}  # Maps element/property names to XSD datatypes
        self.attribute_datatype_map = {}  # Maps attribute names to XSD datatypes
        self.enum_map = {}  # Maps enumeration values to SKOS concepts
        
        # Cache for faster lookups
        self._class_cache = {}
        self._property_cache = {}
        self._datatype_cache = {}
        
        logging.debug("Initialized XML to RDF mapping")
    
    def initialize(self, ontology: Graph) -> None:
        """
        Initialize the mapping from the ontology.
        
        Args:
            ontology: rdflib.Graph containing the OWL ontology
        """
        logging.info("Initializing mapping from ontology")
        
        # Extract classes
        self._extract_classes(ontology)
        
        # Extract properties
        self._extract_properties(ontology)
        
        # Extract enumerations (SKOS concepts)
        self._extract_enumerations(ontology)
        
        logging.info(f"Mapping initialized with {len(self.class_map)} classes, "
                    f"{len(self.property_map)} properties, and "
                    f"{len(self.enum_map)} enumeration values")
    
    def _extract_classes(self, ontology: Graph) -> None:
        """
        Extract OWL classes from the ontology.
        
        Args:
            ontology: rdflib.Graph containing the OWL ontology
        """
        # Find all OWL classes
        for class_uri in ontology.subjects(RDF.type, OWL.Class):
            # Get the class label (if available)
            for _, _, label in ontology.triples((class_uri, RDFS.label, None)):
                class_name = str(label)
                self.class_map[class_name] = class_uri
                logging.debug(f"Mapped class: {class_name} -> {class_uri}")
                break
            
            # If no label, use the local name from the URI
            if class_uri not in self.class_map.values():
                class_name = self._get_local_name(class_uri)
                if class_name:
                    self.class_map[class_name] = class_uri
                    logging.debug(f"Mapped class (from URI): {class_name} -> {class_uri}")
    
    def _extract_properties(self, ontology: Graph) -> None:
        """
        Extract OWL properties from the ontology.
        
        Args:
            ontology: rdflib.Graph containing the OWL ontology
        """
        # Find all OWL datatype properties
        for prop_uri in ontology.subjects(RDF.type, OWL.DatatypeProperty):
            self._process_property(ontology, prop_uri, is_datatype=True)
        
        # Find all OWL object properties
        for prop_uri in ontology.subjects(RDF.type, OWL.ObjectProperty):
            self._process_property(ontology, prop_uri, is_datatype=False)
    
    def _process_property(self, ontology: Graph, prop_uri: URIRef, is_datatype: bool) -> None:
        """
        Process an OWL property and add it to the appropriate maps.
        
        Args:
            ontology: rdflib.Graph containing the OWL ontology
            prop_uri: URI of the property
            is_datatype: Whether this is a datatype property
        """
        # Get the property label (if available)
        prop_name = None
        for _, _, label in ontology.triples((prop_uri, RDFS.label, None)):
            prop_name = str(label)
            break
        
        # If no label, use the local name from the URI
        if not prop_name:
            prop_name = self._get_local_name(prop_uri)
        
        if not prop_name:
            return
        
        # Add to property map
        self.property_map[prop_name] = prop_uri
        
        # For datatype properties, check if it's for an attribute or element text
        if is_datatype:
            # Check if this property is for an attribute (by convention or comment)
            is_attribute = False
            for _, _, comment in ontology.triples((prop_uri, RDFS.comment, None)):
                if "attribute" in str(comment).lower():
                    is_attribute = True
                    break
            
            # Add to the appropriate map
            if is_attribute:
                self.attribute_property_map[prop_name] = prop_uri
                logging.debug(f"Mapped attribute property: {prop_name} -> {prop_uri}")
                
                # Extract datatype for the attribute
                for _, _, range_uri in ontology.triples((prop_uri, RDFS.range, None)):
                    if str(range_uri).startswith(str(XSD)):
                        self.attribute_datatype_map[prop_name] = range_uri
                        logging.debug(f"Mapped attribute datatype: {prop_name} -> {range_uri}")
                        break
            else:
                # Assume it's for element text content
                self.text_property_map[prop_name] = prop_uri
                logging.debug(f"Mapped text property: {prop_name} -> {prop_uri}")
                
                # Extract datatype
                for _, _, range_uri in ontology.triples((prop_uri, RDFS.range, None)):
                    if str(range_uri).startswith(str(XSD)):
                        self.datatype_map[prop_name] = range_uri
                        logging.debug(f"Mapped datatype: {prop_name} -> {range_uri}")
                        break
    
    def _extract_enumerations(self, ontology: Graph) -> None:
        """
        Extract SKOS concepts (enumerations) from the ontology.
        
        Args:
            ontology: rdflib.Graph containing the OWL ontology
        """
        # Find all SKOS concepts
        for concept_uri in ontology.subjects(RDF.type, URIRef("http://www.w3.org/2004/02/skos/core#Concept")):
            # Get the concept scheme
            scheme_uri = None
            for _, _, scheme in ontology.triples((concept_uri, URIRef("http://www.w3.org/2004/02/skos/core#inScheme"), None)):
                scheme_uri = scheme
                break
            
            if not scheme_uri:
                continue
            
            # Get the scheme name
            scheme_name = None
            for _, _, label in ontology.triples((scheme_uri, RDFS.label, None)):
                scheme_name = str(label)
                break
            
            if not scheme_name:
                scheme_name = self._get_local_name(scheme_uri)
            
            if not scheme_name:
                continue
            
            # Get the concept label (enumeration value)
            value = None
            for _, _, label in ontology.triples((concept_uri, URIRef("http://www.w3.org/2004/02/skos/core#prefLabel"), None)):
                value = str(label)
                break
            
            if not value:
                continue
            
            # Add to enum map
            key = f"{scheme_name}:{value}"
            self.enum_map[key] = concept_uri
            logging.debug(f"Mapped enumeration value: {key} -> {concept_uri}")
    
    def _get_local_name(self, uri: URIRef) -> Optional[str]:
        """
        Get the local name from a URI.
        
        Args:
            uri: URI to extract local name from
            
        Returns:
            Local name or None if not found
        """
        uri_str = str(uri)
        
        # Try to extract local name after the last # or /
        if '#' in uri_str:
            return uri_str.split('#')[-1]
        elif '/' in uri_str:
            return uri_str.split('/')[-1]
        
        return None
    
    def get_class_uri(self, element_name: str) -> Optional[URIRef]:
        """
        Get the class URI for an XML element.
        
        Args:
            element_name: Name of the XML element
            
        Returns:
            URI of the corresponding OWL class or None if not found
        """
        # Check cache first
        if element_name in self._class_cache:
            return self._class_cache[element_name]
        
        # Try exact match
        if element_name in self.class_map:
            self._class_cache[element_name] = self.class_map[element_name]
            return self.class_map[element_name]
        
        # Try case-insensitive match
        element_name_lower = element_name.lower()
        for name, uri in self.class_map.items():
            if name.lower() == element_name_lower:
                self._class_cache[element_name] = uri
                return uri
        
        # Try with "Type" suffix (common in XSD)
        type_name = f"{element_name}Type"
        if type_name in self.class_map:
            self._class_cache[element_name] = self.class_map[type_name]
            return self.class_map[type_name]
        
        # Not found
        self._class_cache[element_name] = None
        return None
    
    def get_property_uri(self, element_name: str) -> Optional[URIRef]:
        """
        Get the property URI for an XML element.
        
        Args:
            element_name: Name of the XML element
            
        Returns:
            URI of the corresponding OWL property or None if not found
        """
        # Check cache first
        if element_name in self._property_cache:
            return self._property_cache[element_name]
        
        # Try exact match
        if element_name in self.property_map:
            self._property_cache[element_name] = self.property_map[element_name]
            return self.property_map[element_name]
        
        # Try case-insensitive match
        element_name_lower = element_name.lower()
        for name, uri in self.property_map.items():
            if name.lower() == element_name_lower:
                self._property_cache[element_name] = uri
                return uri
        
        # Not found
        self._property_cache[element_name] = None
        return None
    
    def get_attribute_property_uri(self, attr_name: str) -> Optional[URIRef]:
        """
        Get the property URI for an XML attribute.
        
        Args:
            attr_name: Name of the XML attribute
            
        Returns:
            URI of the corresponding OWL property or None if not found
        """
        # Try exact match
        if attr_name in self.attribute_property_map:
            return self.attribute_property_map[attr_name]
        
        # Try case-insensitive match
        attr_name_lower = attr_name.lower()
        for name, uri in self.attribute_property_map.items():
            if name.lower() == attr_name_lower:
                return uri
        
        # Not found
        return None
    
    def get_text_property_uri(self, element_name: str) -> Optional[URIRef]:
        """
        Get the property URI for the text content of an XML element.
        
        Args:
            element_name: Name of the XML element
            
        Returns:
            URI of the corresponding OWL property or None if not found
        """
        # Try exact match
        if element_name in self.text_property_map:
            return self.text_property_map[element_name]
        
        # Try case-insensitive match
        element_name_lower = element_name.lower()
        for name, uri in self.text_property_map.items():
            if name.lower() == element_name_lower:
                return uri
        
        # Try with "Value" suffix (convention for text content)
        value_name = f"{element_name}Value"
        if value_name in self.text_property_map:
            return self.text_property_map[value_name]
        
        # If not found, use the element name as property (common convention)
        return self.get_property_uri(element_name)
    
    def get_datatype(self, element_name: str) -> Optional[URIRef]:
        """
        Get the XSD datatype for an XML element's text content.
        
        Args:
            element_name: Name of the XML element
            
        Returns:
            URI of the corresponding XSD datatype or None if not found
        """
        # Check cache first
        if element_name in self._datatype_cache:
            return self._datatype_cache[element_name]
        
        # Try exact match
        if element_name in self.datatype_map:
            self._datatype_cache[element_name] = self.datatype_map[element_name]
            return self.datatype_map[element_name]
        
        # Try case-insensitive match
        element_name_lower = element_name.lower()
        for name, uri in self.datatype_map.items():
            if name.lower() == element_name_lower:
                self._datatype_cache[element_name] = uri
                return uri
        
        # Default to string if not found
        self._datatype_cache[element_name] = XSD.string
        return XSD.string
    
    def get_attribute_datatype(self, attr_name: str) -> Optional[URIRef]:
        """
        Get the XSD datatype for an XML attribute.
        
        Args:
            attr_name: Name of the XML attribute
            
        Returns:
            URI of the corresponding XSD datatype or None if not found
        """
        # Try exact match
        if attr_name in self.attribute_datatype_map:
            return self.attribute_datatype_map[attr_name]
        
        # Try case-insensitive match
        attr_name_lower = attr_name.lower()
        for name, uri in self.attribute_datatype_map.items():
            if name.lower() == attr_name_lower:
                return uri
        
        # Default to string if not found
        return XSD.string
    
    def get_enum_uri(self, enum_type: str, value: str) -> Optional[URIRef]:
        """
        Get the URI for an enumeration value.
        
        Args:
            enum_type: Type of the enumeration (scheme name)
            value: Enumeration value
            
        Returns:
            URI of the corresponding SKOS concept or None if not found
        """
        key = f"{enum_type}:{value}"
        return self.enum_map.get(key)