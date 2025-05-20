"""
Base rule module for XML to RDF transformation.
Provides the BaseRule class for implementing transformation rules.
"""

from abc import ABC, abstractmethod
from typing import Optional

from lxml import etree
from rdflib import Graph, URIRef

from xml_to_rdf.mapping import XMLtoRDFMapping
from xsd_to_owl.utils import logging


class BaseRule(ABC):
    """
    Base class for XML to RDF transformation rules.
    All rules must inherit from this class and implement the required methods.
    """
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        """
        Get the unique identifier for this rule.
        
        Returns:
            Unique identifier string
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get a human-readable description of this rule.
        
        Returns:
            Description string
        """
        pass
    
    @property
    def priority(self) -> int:
        """
        Get the priority of this rule.
        Rules with higher priority are applied first.
        
        Returns:
            Priority value (default: 100)
        """
        return 100
    
    @abstractmethod
    def matches(self, element: etree._Element, mapping: XMLtoRDFMapping) -> bool:
        """
        Check if this rule applies to the given XML element.
        
        Args:
            element: XML element to check
            mapping: Mapping between XML and RDF
            
        Returns:
            True if the rule applies, False otherwise
        """
        pass
    
    @abstractmethod
    def transform(self, element: etree._Element, graph: Graph, 
                 mapping: XMLtoRDFMapping, parent_uri: Optional[URIRef] = None) -> Optional[URIRef]:
        """
        Transform the XML element to RDF.
        
        Args:
            element: XML element to transform
            graph: RDF graph to add triples to
            mapping: Mapping between XML and RDF
            parent_uri: URI of the parent element (if any)
            
        Returns:
            URI of the transformed element or None
        """
        pass
    
    def log_application(self, element: etree._Element) -> None:
        """
        Log the application of this rule to an element.
        
        Args:
            element: XML element the rule is applied to
        """
        from xml_to_rdf.utils import xml_parsers
        element_name = xml_parsers.get_element_name(element)
        element_path = xml_parsers.get_element_path(element)
        logging.debug(f"Applied rule {self.rule_id} to element {element_name} at {element_path}")