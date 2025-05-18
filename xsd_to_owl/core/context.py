# xsd_to_owl/core/context.py
"""
Context for the XSD to OWL transformation process.
Maintains state during transformation and provides utilities.
"""

from typing import Dict, List, Optional, Set, Any, Union
import rdflib
from lxml import etree
from rdflib import Graph, Namespace, URIRef

from xsd_to_owl.utils import logging
from xsd_to_owl.utils.uri_manager import URIManager


class TransformationContext:
    """
    Context for the XSD to OWL transformation process.
    Maintains state during transformation and provides utilities.
    """
    
    def __init__(self, base_uri: str, uri_encode_method: str = "underscore"):
        """
        Initialize a new transformation context.
        
        Args:
            base_uri: Base URI for generated ontology
            uri_encode_method: Method to encode URIs with spaces
        """
        # Ensure base_uri ends with # or /
        if not base_uri.endswith('#') and not base_uri.endswith('/'):
            base_uri += '#'
            
        self.base_uri = Namespace(base_uri)
        self.graph = Graph()
        
        # Bind common namespaces
        self.graph.bind('owl', rdflib.OWL)
        self.graph.bind('rdfs', rdflib.RDFS)
        self.graph.bind('rdf', rdflib.RDF)
        self.graph.bind('skos', rdflib.SKOS)
        self.graph.bind('xsd', rdflib.XSD)
        self.graph.bind('base', self.base_uri)
        self.graph.bind('dc', rdflib.Namespace("http://purl.org/dc/terms/"))
        self.graph.bind('schema', rdflib.Namespace("http://schema.org/"))
        
        # Store references to common namespaces for easier access
        self.RDF = rdflib.RDF
        self.RDFS = rdflib.RDFS
        self.OWL = rdflib.OWL
        self.SKOS = rdflib.SKOS
        self.XSD = rdflib.XSD
        self.DC = rdflib.Namespace("http://purl.org/dc/terms/")
        self.SCHEMA = rdflib.Namespace("http://schema.org/")
        
        # Create URI manager
        self.uri_manager = URIManager(base_uri, uri_encode_method)
        
        # Store processed elements to avoid duplicates
        # This is a dict, with key = element ID, value = set of rule IDs that processed it
        self._processed_elements: Dict[bytes, Set[str]] = {}
        
        # Current element stack for context tracking
        self._element_stack: List[etree._Element] = []
        
        # Element metadata for sharing information between rules
        self._element_metadata: Dict[bytes, Dict[str, Any]] = {}
        
        # Property name registry for consistent property naming
        self._property_name_registry: Dict[str, URIRef] = {}
        
        logging.debug(f"Initialized transformation context with base URI '{base_uri}'")
    
    # Backward compatibility method for old code
    def get_safe_uri(self, base_uri, local_part, is_property=False):
        """
        Backward compatibility method for old code.
        
        Args:
            base_uri: The base URI (namespace) - ignored, using context's base URI
            local_part: The local part to be appended to the base URI
            is_property: Whether this is a property name (affects casing)
            
        Returns:
            A properly formed URI
        """
        logging.debug(f"Using deprecated get_safe_uri method for {local_part}")
        if is_property:
            return self.uri_manager.get_property_uri(local_part, is_datatype=True)
        else:
            return self.uri_manager.get_class_uri(local_part)
    
    # Backward compatibility method for old code
    def get_concept_uri(self, scheme_uri, value):
        """
        Backward compatibility method for old code.
        
        Args:
            scheme_uri: URI of the concept scheme
            value: The enumeration value
            
        Returns:
            URI for the concept
        """
        logging.debug(f"Using deprecated get_concept_uri method for {value} in scheme {scheme_uri}")
        return self.uri_manager.get_concept_uri(scheme_uri, value)
    
    def enter_element(self, element: etree._Element) -> None:
        """
        Record entering an element during traversal.
        
        Args:
            element: The XSD element being entered
        """
        self._element_stack.append(element)
    
    def exit_element(self) -> None:
        """
        Record exiting an element during traversal.
        """
        if self._element_stack:
            self._element_stack.pop()
    
    def get_parent_element(self) -> Optional[etree._Element]:
        """
        Get the parent of the current element.
        
        Returns:
            The parent element or None
        """
        if len(self._element_stack) > 1:
            return self._element_stack[-2]
        return None
    
    def is_processed(self, element: etree._Element, rule_id: str) -> bool:
        """
        Check if an element has been processed by a specific rule.
        
        Args:
            element: The XSD element to check
            rule_id: Rule ID to check
            
        Returns:
            bool: True if processed by this rule
        """
        element_id = etree.tostring(element)
        if element_id not in self._processed_elements:
            return False
            
        return rule_id in self._processed_elements[element_id]
    
    def mark_processed(self, element: etree._Element, rule_id: str) -> None:
        """
        Mark an element as processed by a rule.
        
        Args:
            element: The XSD element to mark
            rule_id: ID of the rule that processed it
        """
        element_id = etree.tostring(element)
        if element_id not in self._processed_elements:
            self._processed_elements[element_id] = set()
            
        self._processed_elements[element_id].add(rule_id)
        logging.debug(f"Marked element {element.tag} as processed by rule {rule_id}")
    
    def get_type_reference(self, type_name: str) -> URIRef:
        """
        Get a URI reference for an XSD type.
        
        Args:
            type_name: Name of the type
            
        Returns:
            URI for the type
        """
        # Handle built-in XSD types
        if ':' in type_name:
            prefix, local = type_name.split(':', 1)
            if prefix in ('xs', 'xsd'):
                return getattr(self.XSD, local)
                
        # Custom types are references to resources in the base namespace
        return self.uri_manager.get_class_uri(type_name)
    
    def register_property_uri(self, property_name: str, uri: URIRef) -> None:
        """
        Register a canonical URI for a property name.
        
        Args:
            property_name: The name of the property
            uri: The URI to register
        """
        # Normalize property name to lowercase for consistent lookups
        normalized_name = self.uri_manager._lower_case_initial(property_name)
        self._property_name_registry[normalized_name] = uri
        logging.debug(f"Registered property URI {uri} for name '{property_name}'")
    
    def get_property_uri(self, property_name: str) -> Optional[URIRef]:
        """
        Get the canonical URI for a property name if registered.
        
        Args:
            property_name: The name of the property
            
        Returns:
            The registered URI or None if not found
        """
        normalized_name = self.uri_manager._lower_case_initial(property_name)
        return self._property_name_registry.get(normalized_name)
    
    def add_element_metadata(self, element: etree._Element, metadata: Dict[str, Any]) -> None:
        """
        Add metadata to an element for use by other rules.
        
        Args:
            element: The XSD element
            metadata: Dictionary of metadata to store
        """
        element_id = etree.tostring(element)
        
        # Merge with existing metadata if present
        existing = self._element_metadata.get(element_id, {})
        existing.update(metadata)
        self._element_metadata[element_id] = existing
        
        logging.debug(f"Added metadata to element {element.tag}: {metadata}")
    
    def get_element_metadata(self, element: etree._Element) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an element if it exists.
        
        Args:
            element: The XSD element
            
        Returns:
            Dictionary of metadata or None if not found
        """
        element_id = etree.tostring(element)
        return self._element_metadata.get(element_id)
    
    def generate_rule_application_report(self) -> str:
        """
        Generates a detailed report of what rules were applied to each element.
        
        Returns:
            A formatted string report showing elements and the rules that processed them.
        """
        report = ["Rule Application Report"]
        report.append("=" * 80)
        
        # Group by element
        element_to_rules = {}
        for element_id, rule_ids in self._processed_elements.items():
            # Try to extract a more readable element name
            try:
                # Parse the element from its string representation
                element = etree.fromstring(element_id)
                element_name = f"{element.tag.split('}')[-1]}"
                if 'name' in element.attrib:
                    element_name += f" name='{element.attrib['name']}'"
                elif 'ref' in element.attrib:
                    element_name += f" ref='{element.attrib['ref']}'"
            except:
                # Fallback if parsing fails
                element_name = f"Element ID: {element_id[:50]}..."
                
            element_to_rules[element_name] = sorted(list(rule_ids))
            
        # Sort elements by name for readability
        for element_name in sorted(element_to_rules.keys()):
            rule_ids = element_to_rules[element_name]
            
            report.append(f"\nElement: {element_name}")
            report.append("-" * 80)
            
            if not rule_ids:
                report.append("  No rules applied")
            else:
                for rule_id in rule_ids:
                    report.append(f"  • {rule_id}")
                    
        return "\n".join(report)
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the generated ontology.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "classes": len(list(self.graph.subjects(self.RDF.type, self.OWL.Class))),
            "datatype_properties": len(list(self.graph.subjects(self.RDF.type, self.OWL.DatatypeProperty))),
            "object_properties": len(list(self.graph.subjects(self.RDF.type, self.OWL.ObjectProperty))),
            "concept_schemes": len(list(self.graph.subjects(self.RDF.type, self.SKOS.ConceptScheme))),
            "concepts": len(list(self.graph.subjects(self.RDF.type, self.SKOS.Concept))),
            "total_triples": len(self.graph)
        }
        return stats