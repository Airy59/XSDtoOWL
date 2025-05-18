# xsd_to_owl/rules/ontology_rules.py
"""
Rules for handling ontology metadata, annotations, and header information.
These rules are responsible for setting the ontology IRI, adding annotations,
and including statistics about the ontology contents.
"""

from typing import Optional, Any
from datetime import datetime

from lxml import etree
from rdflib import URIRef, Literal, BNode

from xsd_to_owl.rules.base import BaseRule
from xsd_to_owl.utils import logging


class OntologyHeaderRule(BaseRule):
    """
    Rule for creating the ontology header and setting the ontology IRI.
    This rule creates the ontology declaration and sets basic metadata.
    """
    
    @property
    def rule_id(self) -> str:
        return "OntologyHeaderRule"
    
    @property
    def description(self) -> str:
        return "Creates the ontology declaration and sets the ontology IRI"
    
    @property
    def priority(self) -> int:
        # High priority to ensure it runs early
        return 1000
    
    def matches(self, element: etree._Element, context: Any) -> bool:
        # Only match the root schema element
        is_schema = element.tag.endswith('schema') and element.getparent() is None
        logging.debug(f"OntologyHeaderRule.matches: {is_schema} for element {element.tag}")
        return is_schema
    
    def transform(self, element: etree._Element, context: Any) -> Optional[URIRef]:
        # Check if already processed
        if self.is_processed(element, context):
            logging.debug(f"OntologyHeaderRule.transform: Element already processed")
            return None
        
        # Get the target namespace if available
        target_namespace = element.get('targetNamespace')
        logging.debug(f"OntologyHeaderRule.transform: Target namespace: {target_namespace}")
        
        # Create ontology IRI - use target namespace if available, otherwise use base URI
        ontology_iri = URIRef(target_namespace if target_namespace else str(context.base_uri)[:-1])
        logging.debug(f"OntologyHeaderRule.transform: Created ontology IRI: {ontology_iri}")
        
        # Declare the ontology
        context.graph.add((ontology_iri, context.RDF.type, context.OWL.Ontology))
        
        # Add creation date
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        context.graph.add((ontology_iri, context.OWL.versionInfo, Literal(now)))
        logging.debug(f"OntologyHeaderRule.transform: Added version info: {now}")
        
        # Mark as processed
        self.mark_processed(element, context)
        
        return ontology_iri
    
    def is_processed(self, element: etree._Element, context: Any) -> bool:
        """Check if this rule has already been applied to the element."""
        return context.is_processed(element, self.rule_id)
    
    def mark_processed(self, element: etree._Element, context: Any) -> None:
        """Mark the element as processed by this rule."""
        context.mark_processed(element, self.rule_id)


class OntologyAnnotationRule(BaseRule):
    """
    Rule for adding annotations to the ontology.
    This rule adds metadata such as title, description, and statistics.
    """
    
    @property
    def rule_id(self) -> str:
        return "OntologyAnnotationRule"
    
    @property
    def description(self) -> str:
        return "Adds annotations and statistics to the ontology"
    
    @property
    def priority(self) -> int:
        # Low priority to ensure it runs at the end when all resources are created
        return 10
    
    def matches(self, element: etree._Element, context: Any) -> bool:
        # Only match the root schema element
        is_schema = element.tag.endswith('schema') and element.getparent() is None
        logging.debug(f"OntologyAnnotationRule.matches: {is_schema} for element {element.tag}")
        return is_schema
    
    def transform(self, element: etree._Element, context: Any) -> Optional[URIRef]:
        # Check if already processed
        if self.is_processed(element, context):
            logging.debug(f"OntologyAnnotationRule.transform: Element already processed")
            return None
        
        # Find the ontology IRI
        ontology_iris = list(context.graph.subjects(context.RDF.type, context.OWL.Ontology))
        logging.debug(f"OntologyAnnotationRule.transform: Found {len(ontology_iris)} ontology IRIs")
        
        if not ontology_iris:
            # If no ontology IRI exists, create one
            target_namespace = element.get('targetNamespace')
            ontology_iri = URIRef(target_namespace if target_namespace else str(context.base_uri)[:-1])
            context.graph.add((ontology_iri, context.RDF.type, context.OWL.Ontology))
            logging.debug(f"OntologyAnnotationRule.transform: Created new ontology IRI: {ontology_iri}")
        else:
            ontology_iri = ontology_iris[0]
            logging.debug(f"OntologyAnnotationRule.transform: Using existing ontology IRI: {ontology_iri}")
        
        # Add basic annotations
        schema_id = element.get('id')
        if schema_id:
            context.graph.add((ontology_iri, context.RDFS.label, Literal(f"Ontology for {schema_id}")))
            logging.debug(f"OntologyAnnotationRule.transform: Added label with schema ID: {schema_id}")
        else:
            context.graph.add((ontology_iri, context.RDFS.label, Literal("XSD to OWL Transformed Ontology")))
            logging.debug(f"OntologyAnnotationRule.transform: Added default label")
        
        # Add documentation if available
        doc = self.get_documentation(element)
        if doc:
            context.graph.add((ontology_iri, context.RDFS.comment, Literal(doc)))
            logging.debug(f"OntologyAnnotationRule.transform: Added documentation from schema")
        else:
            context.graph.add((ontology_iri, context.RDFS.comment, Literal("Ontology generated from XSD schema using xsd_to_owl transformation framework")))
            logging.debug(f"OntologyAnnotationRule.transform: Added default documentation")
        
        # Add statistics as annotations
        stats = context.get_statistics()
        logging.debug(f"OntologyAnnotationRule.transform: Got statistics: {stats}")
        
        # Add statistics directly to the ontology
        context.graph.add((ontology_iri, context.RDFS.comment, Literal(f"Total triples: {stats['total_triples']}")))
        context.graph.add((ontology_iri, context.RDFS.comment, Literal(f"OWL Classes: {stats['classes']}")))
        context.graph.add((ontology_iri, context.RDFS.comment, Literal(f"Datatype Properties: {stats['datatype_properties']}")))
        context.graph.add((ontology_iri, context.RDFS.comment, Literal(f"Object Properties: {stats['object_properties']}")))
        context.graph.add((ontology_iri, context.RDFS.comment, Literal(f"SKOS Concept Schemes: {stats['concept_schemes']}")))
        context.graph.add((ontology_iri, context.RDFS.comment, Literal(f"SKOS Concepts: {stats['concepts']}")))
        logging.debug(f"OntologyAnnotationRule.transform: Added statistics as comments")
        
        # Mark as processed
        self.mark_processed(element, context)
        
        return ontology_iri
    
    def is_processed(self, element: etree._Element, context: Any) -> bool:
        """Check if this rule has already been applied to the element."""
        return context.is_processed(element, self.rule_id)
    
    def mark_processed(self, element: etree._Element, context: Any) -> None:
        """Mark the element as processed by this rule."""
        context.mark_processed(element, self.rule_id)