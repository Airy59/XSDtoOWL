# xsd_to_owl/rules/base.py
"""
Base classes for XSD to OWL transformation rules.
Provides common functionality for all rule types.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Tuple

import rdflib
from lxml import etree
from rdflib import URIRef, Literal

from xsd_to_owl.utils import logging

# Define XML Schema namespace constant
XS_NS = "{http://www.w3.org/2001/XMLSchema}"


class BaseRule(ABC):
    """
    Base class for all transformation rules.
    Defines the common interface and functionality.
    """
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for the rule."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the rule."""
        pass
    
    @property
    def priority(self) -> int:
        """
        Priority of this rule. Higher values indicate higher priority.
        Default is 100. Override in subclasses as needed.
        """
        return 100
    
    @abstractmethod
    def matches(self, element: etree._Element, context: Any) -> bool:
        """
        Determines if this rule should be applied to the given element.
        
        Args:
            element: The XSD element to check
            context: The transformation context
            
        Returns:
            bool: True if the rule should be applied
        """
        pass
    
    @abstractmethod
    def transform(self, element: etree._Element, context: Any) -> Optional[URIRef]:
        """
        Transforms the element according to the rule.
        
        Args:
            element: The XSD element to transform
            context: The transformation context
            
        Returns:
            The URI of the created resource or None
        """
        pass
    
    def get_element_name(self, element: etree._Element) -> Optional[str]:
        """
        Get the name of an element.
        
        Args:
            element: The XSD element
            
        Returns:
            The name attribute or None if not present
        """
        return element.get('name')
    
    def get_element_type(self, element: etree._Element) -> Optional[str]:
        """
        Get the type of an element.
        
        Args:
            element: The XSD element
            
        Returns:
            The type attribute or None if not present
        """
        return element.get('type')
    
    def get_element_ref(self, element: etree._Element) -> Optional[str]:
        """
        Get the ref attribute of an element.
        
        Args:
            element: The XSD element
            
        Returns:
            The ref attribute or None if not present
        """
        return element.get('ref')
    
    def get_documentation(self, element: etree._Element) -> Optional[str]:
        """
        Extract documentation from an element.
        
        Args:
            element: The XSD element
            
        Returns:
            The documentation text or None if not found
        """
        # Look for annotation/documentation
        annotation = element.find(f".//{XS_NS}annotation")
        if annotation is None:
            return None
        
        documentation = annotation.find(f".//{XS_NS}documentation")
        if documentation is None or not documentation.text:
            return None
        
        # Clean up the documentation text
        doc_text = documentation.text.strip()
        return doc_text if doc_text else None
    
    def find_parent_element(self, element: etree._Element) -> Optional[etree._Element]:
        """
        Find the parent element in the XSD hierarchy.
        
        Args:
            element: The XSD element
            
        Returns:
            The parent element or None if not found
        """
        return element.getparent()
    
    def is_functional(self, element: etree._Element) -> bool:
        """
        Determine if an element should be a functional property.
        
        Args:
            element: The XSD element
            
        Returns:
            True if the element should be a functional property
        """
        # Check minOccurs and maxOccurs
        max_occurs = element.get('maxOccurs')
        if max_occurs is not None and max_occurs != '1' and max_occurs != 'unbounded':
            try:
                if int(max_occurs) > 1:
                    return False
            except ValueError:
                pass
        
        # Default to functional if not specified otherwise
        return True
    
    def log_rule_application(self, element: etree._Element, success: bool = True) -> None:
        """
        Log the application of this rule to an element.
        
        Args:
            element: The XSD element
            success: Whether the rule was successfully applied
        """
        element_tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        element_name = self.get_element_name(element)
        logging.log_rule_application(self.rule_id, element_tag, element_name, success)


class BaseClassRule(BaseRule):
    """
    Base class for rules that create OWL classes.
    Provides common functionality for class creation.
    """
    
    def create_class(self, name: str, context: Any) -> URIRef:
        """
        Create an OWL class in the graph.
        
        Args:
            name: The name of the class
            context: The transformation context
            
        Returns:
            The URI of the created class
        """
        # Get URI for the class
        class_uri = context.uri_manager.get_class_uri(name)
        
        # Create owl:Class
        context.graph.add((class_uri, context.RDF.type, context.OWL.Class))
        context.graph.add((class_uri, context.RDFS.label, Literal(name)))
        
        logging.debug(f"Created OWL class: {class_uri} with label '{name}'")
        return class_uri
    
    def add_class_documentation(self, class_uri: URIRef, doc_text: str, context: Any) -> None:
        """
        Add documentation to a class.
        
        Args:
            class_uri: The URI of the class
            doc_text: The documentation text
            context: The transformation context
        """
        if doc_text:
            context.graph.add((class_uri, context.SKOS.definition, Literal(doc_text)))
            logging.debug(f"Added documentation to class {class_uri}")


class BasePropertyRule(BaseRule):
    """
    Base class for rules that create OWL properties.
    Provides common functionality for property creation.
    """
    
    def create_datatype_property(self, name: str, domain_uri: Optional[URIRef], 
                                range_uri: URIRef, context: Any) -> URIRef:
        """
        Create a datatype property in the graph.
        
        Args:
            name: The name of the property
            domain_uri: The URI of the domain class (optional)
            range_uri: The URI of the range datatype
            context: The transformation context
            
        Returns:
            The URI of the created property
        """
        # Get URI for the property
        property_uri = context.uri_manager.get_property_uri(name, is_datatype=True)
        
        # Create owl:DatatypeProperty
        context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
        context.graph.add((property_uri, context.RDFS.label, Literal(name)))
        
        # Add domain if provided
        if domain_uri:
            context.graph.add((property_uri, context.RDFS.domain, domain_uri))
        
        # Add range
        context.graph.add((property_uri, context.RDFS.range, range_uri))
        
        logging.debug(f"Created datatype property: {property_uri} with label '{name}'")
        return property_uri
    
    def create_object_property(self, name: str, domain_uri: Optional[URIRef], 
                              range_uri: URIRef, context: Any) -> URIRef:
        """
        Create an object property in the graph.
        
        Args:
            name: The name of the property
            domain_uri: The URI of the domain class (optional)
            range_uri: The URI of the range class
            context: The transformation context
            
        Returns:
            The URI of the created property
        """
        # Get URI for the property
        property_uri = context.uri_manager.get_property_uri(name, is_datatype=False)
        
        # Create owl:ObjectProperty
        context.graph.add((property_uri, context.RDF.type, context.OWL.ObjectProperty))
        context.graph.add((property_uri, context.RDFS.label, Literal(name)))
        
        # Add domain if provided
        if domain_uri:
            context.graph.add((property_uri, context.RDFS.domain, domain_uri))
        
        # Add range
        context.graph.add((property_uri, context.RDFS.range, range_uri))
        
        logging.debug(f"Created object property: {property_uri} with label '{name}'")
        return property_uri
    
    def add_property_documentation(self, property_uri: URIRef, doc_text: str, context: Any) -> None:
        """
        Add documentation to a property.
        
        Args:
            property_uri: The URI of the property
            doc_text: The documentation text
            context: The transformation context
        """
        if doc_text:
            context.graph.add((property_uri, context.SKOS.definition, Literal(doc_text)))
            logging.debug(f"Added documentation to property {property_uri}")
    
    def add_functional_property(self, property_uri: URIRef, context: Any) -> None:
        """
        Mark a property as functional.
        
        Args:
            property_uri: The URI of the property
            context: The transformation context
        """
        context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))
        logging.debug(f"Marked property {property_uri} as functional")
    
    def determine_property_type(self, element: etree._Element, context: Any) -> str:
        """
        Determine if an element should be a datatype or object property.
        
        Args:
            element: The XSD element
            context: The transformation context
            
        Returns:
            "datatype" or "object"
        """
        from xsd_to_owl.config.special_cases import (
            is_forced_datatype_property, is_forced_object_property,
            is_datatype_property_type, should_never_be_object_property
        )
        
        name = self.get_element_name(element)
        type_name = self.get_element_type(element)
        
        # Check special cases first
        if name and is_forced_datatype_property(name):
            logging.debug(f"Element {name} forced to be a datatype property by configuration")
            return "datatype"
        
        if name and should_never_be_object_property(name, type_name):
            logging.debug(f"Element {name} should never be an object property by configuration or type")
            return "datatype"
        
        if name and is_forced_object_property(name):
            logging.debug(f"Element {name} forced to be an object property by configuration")
            return "object"
        
        # Check type-based rules
        if type_name:
            # Check for built-in XSD types or numeric types
            if ':' in type_name or type_name.startswith('Numeric') or is_datatype_property_type(type_name):
                return "datatype"
            
            # Otherwise, assume it's a reference to a complex type
            return "object"
        
        # Check for inline type definitions
        has_simple_type = element.find(f".//{XS_NS}simpleType") is not None
        has_complex_type = element.find(f".//{XS_NS}complexType") is not None
        
        if has_simple_type and not has_complex_type:
            return "datatype"
        
        if has_complex_type:
            return "object"
        
        # Default to datatype if we can't determine
        return "datatype"


class BaseEnumRule(BaseRule):
    """
    Base class for rules that create SKOS concept schemes.
    Provides common functionality for enumeration handling.
    """
    
    def create_concept_scheme(self, name: str, context: Any) -> URIRef:
        """
        Create a SKOS concept scheme in the graph.
        
        Args:
            name: The name of the concept scheme
            context: The transformation context
            
        Returns:
            The URI of the created concept scheme
        """
        # Get URI for the concept scheme
        scheme_uri = context.uri_manager.get_class_uri(name)
        
        # Create skos:ConceptScheme
        context.graph.add((scheme_uri, context.RDF.type, context.SKOS.ConceptScheme))
        context.graph.add((scheme_uri, context.RDFS.label, Literal(name)))
        
        logging.debug(f"Created concept scheme: {scheme_uri} with label '{name}'")
        return scheme_uri
    
    def create_concept(self, scheme_uri: URIRef, value: str, context: Any) -> URIRef:
        """
        Create a SKOS concept in the graph.
        
        Args:
            scheme_uri: The URI of the concept scheme
            value: The enumeration value
            context: The transformation context
            
        Returns:
            The URI of the created concept
        """
        # Get URI for the concept
        concept_uri = context.uri_manager.get_concept_uri(scheme_uri, value)
        
        # Create skos:Concept
        context.graph.add((concept_uri, context.RDF.type, context.SKOS.Concept))
        context.graph.add((concept_uri, context.SKOS.inScheme, scheme_uri))
        context.graph.add((concept_uri, context.SKOS.prefLabel, Literal(value)))
        
        logging.debug(f"Created concept: {concept_uri} with label '{value}'")
        return concept_uri
    
    def add_concept_documentation(self, concept_uri: URIRef, doc_text: str, context: Any) -> None:
        """
        Add documentation to a concept.
        
        Args:
            concept_uri: The URI of the concept
            doc_text: The documentation text
            context: The transformation context
        """
        if doc_text:
            context.graph.add((concept_uri, context.SKOS.definition, Literal(doc_text)))
            logging.debug(f"Added documentation to concept {concept_uri}")
    
    def extract_enum_values(self, element: etree._Element) -> List[Tuple[str, Optional[str]]]:
        """
        Extract enumeration values and their documentation from an element.
        
        Args:
            element: The XSD element
            
        Returns:
            List of tuples (value, documentation)
        """
        values = []
        
        # Find restriction element
        restriction = element.find(f".//{XS_NS}restriction")
        if restriction is None:
            return values
        
        # Find all enumeration elements
        for enum in restriction.findall(f".//{XS_NS}enumeration"):
            value = enum.get('value')
            if value:
                doc = self.get_documentation(enum)
                values.append((value, doc))
        
        return values