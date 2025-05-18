# xsd_to_owl/transform.py
"""
Main transformer module for XSD to OWL/SKOS transformation.
Provides the XSDtoOWLTransformer class for orchestrating the transformation process.
"""

import os
from typing import Dict, List, Optional, Union, Any, Type

import rdflib
from lxml import etree
from rdflib import Graph, URIRef

from xsd_to_owl.core.context import TransformationContext
from xsd_to_owl.core.pipeline import (
    TransformationPipeline, ClassCreationPhase, PropertyCreationPhase,
    EnumerationPhase, RelationshipPhase, CleanupPhase
)
from xsd_to_owl.rules.base import BaseRule
from xsd_to_owl.utils import logging


class XSDtoOWLTransformer:
    """
    Main transformer class for XSD to OWL/SKOS transformation.
    Uses a pipeline of rules to transform XSD elements into OWL/SKOS constructs.
    """
    
    def __init__(self, uri_encode_method: str = "underscore"):
        """
        Initialize a new transformer with an empty pipeline.
        
        Args:
            uri_encode_method: Method to encode URIs with spaces. Options:
                - "percent": Use %20 encoding (standard)
                - "underscore": Replace spaces with underscores
                - "camelcase": Remove spaces and capitalize words
                - "dash": Replace spaces with dashes
        """
        self.pipeline = TransformationPipeline()
        self.uri_encode_method = uri_encode_method
        
        # Initialize rule collections for each phase
        self._class_rules: List[BaseRule] = []
        self._property_rules: List[BaseRule] = []
        self._enum_rules: List[BaseRule] = []
        self._relationship_rules: List[BaseRule] = []
        self._cleanup_rules: List[BaseRule] = []
        
        logging.debug(f"Initialized transformer with URI encoding method: {uri_encode_method}")
    
    def register_rule(self, rule: BaseRule, phase: Optional[str] = None) -> 'XSDtoOWLTransformer':
        """
        Register a transformation rule.
        
        Args:
            rule: A rule implementation
            phase: Optional phase to register the rule with (auto-detected if not provided)
            
        Returns:
            self for chaining
        """
        # Auto-detect phase based on rule class if not provided
        if phase is None:
            rule_class_name = rule.__class__.__name__.lower()
            
            if 'class' in rule_class_name:
                phase = 'class'
            elif 'property' in rule_class_name:
                phase = 'property'
            elif 'enum' in rule_class_name:
                phase = 'enum'
            elif 'relation' in rule_class_name:
                phase = 'relationship'
            elif 'cleanup' in rule_class_name:
                phase = 'cleanup'
            else:
                # Default to property phase if can't determine
                phase = 'property'
        
        # Add to the appropriate rule collection
        if phase == 'class':
            self._class_rules.append(rule)
        elif phase == 'property':
            self._property_rules.append(rule)
        elif phase == 'enum':
            self._enum_rules.append(rule)
        elif phase == 'relationship':
            self._relationship_rules.append(rule)
        elif phase == 'cleanup':
            self._cleanup_rules.append(rule)
        else:
            raise ValueError(f"Unknown phase: {phase}")
        
        logging.debug(f"Registered rule {rule.rule_id} in phase {phase}")
        return self
    
    def transform(self, xsd_file: Union[str, bytes], 
                 base_uri: str = "http://example.org/", 
                 uri_encode_method: Optional[str] = None) -> Graph:
        """
        Transform an XSD file to OWL/SKOS ontology.
        
        Args:
            xsd_file: Path to XSD file or XML string/bytes
            base_uri: Base URI for generated ontology
            uri_encode_method: Method to encode URIs (overrides instance setting if provided)
            
        Returns:
            rdflib.Graph containing the ontology
        """
        # Use provided URI encoding method or fall back to instance setting
        encoding_method = uri_encode_method or self.uri_encode_method
        
        # Initialize context with base URI
        context = TransformationContext(base_uri, encoding_method)
        
        # Parse XSD file or content
        parser = etree.XMLParser(remove_comments=True)
        
        try:
            # If xsd_file is a path to a file, read the file
            if isinstance(xsd_file, str) and os.path.isfile(xsd_file):
                logging.info(f"Parsing XSD file: {xsd_file}")
                xsd_root = etree.parse(xsd_file, parser).getroot()
            # If xsd_file is a string of XML content
            elif isinstance(xsd_file, str):
                logging.info("Parsing XSD from string content")
                xsd_root = etree.fromstring(xsd_file.encode('utf-8'), parser)
            # If xsd_file is already bytes
            else:
                logging.info("Parsing XSD from bytes content")
                xsd_root = etree.fromstring(xsd_file, parser)
        except Exception as e:
            logging.error(f"Failed to parse XSD: {e}")
            raise
        
        # Configure the pipeline with rules
        self._configure_pipeline()
        
        # Log transformation start
        logging.log_transformation_start(
            xsd_file if isinstance(xsd_file, str) and os.path.isfile(xsd_file) else "in-memory content",
            base_uri
        )
        
        # Execute the transformation pipeline
        try:
            self.pipeline.execute(xsd_root, context)
        except Exception as e:
            logging.error(f"Transformation failed: {e}")
            raise
        
        # Log transformation completion
        stats = context.get_statistics()
        logging.log_transformation_complete(stats["total_triples"], stats)
        
        # Generate and log rule application report
        report = context.generate_rule_application_report()
        logging.debug(report)
        
        return context.graph
    
    def _configure_pipeline(self) -> None:
        """
        Configure the transformation pipeline with registered rules.
        """
        # Clear existing phases
        self.pipeline = TransformationPipeline()
        
        # Create phases with registered rules
        class_phase = ClassCreationPhase(self._class_rules)
        property_phase = PropertyCreationPhase(self._property_rules)
        enum_phase = EnumerationPhase(self._enum_rules)
        relationship_phase = RelationshipPhase(self._relationship_rules)
        cleanup_phase = CleanupPhase(self._cleanup_rules)
        
        # Replace default phases with our configured ones
        self.pipeline.phases = [
            class_phase,
            property_phase,
            enum_phase,
            relationship_phase,
            cleanup_phase
        ]
        
        logging.debug("Configured transformation pipeline")
    
    def serialize(self, graph: Graph, format: str = "turtle") -> str:
        """
        Serialize the ontology graph to the specified format.
        
        Args:
            graph: rdflib.Graph to serialize
            format: Output_owl format (turtle, xml, etc.)
            
        Returns:
            String serialization of the graph
        """
        return graph.serialize(format=format)
    
    def save(self, graph: Graph, output_file: str, format: str = "turtle") -> None:
        """
        Save the ontology graph to a file.
        
        Args:
            graph: rdflib.Graph to save
            output_file: Path to save the ontology
            format: Output_owl format (turtle, xml, etc.)
        """
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Serialize and save
        graph.serialize(destination=output_file, format=format)
        logging.info(f"Saved ontology to {output_file} in {format} format")


def create_default_transformer(uri_encode_method: str = "underscore") -> XSDtoOWLTransformer:
    """
    Create a transformer with default rules.
    
    Args:
        uri_encode_method: Method to encode URIs with spaces
        
    Returns:
        A configured XSDtoOWLTransformer
    """
    # Import rules here to avoid circular imports
    from xsd_to_owl.rules.class_rules import (
        DetectSimpleTypeRule,
        NamedComplexTypeRule,
        TargetClassCreationRule,
        TopLevelNamedElementRule,
        AnonymousComplexTypeRule,
    )
    from xsd_to_owl.rules.property_rules import (
        SimpleTypePropertyRule,
        InlineSimpleTypePropertyRule,
        ComplexTypeReferenceRule,
        NumericTypePropertyRule,
        TopLevelSimpleElementRule,
        ElementReferenceRule,
        ChildElementPropertyRule,
        ComplexElementPropertyRule,
        SandwichElementPropertyRule,
        ReferenceTrackingRule,
        ReferencedElementDomainRule,
        DomainFixerRule,
        PropertyTypeFixerRule,
    )
    from xsd_to_owl.rules.enum_rules import (
        EnhancedNamedEnumTypeRule,
        EnhancedAnonymousEnumTypeRule,
    )
    
    # Create transformer
    transformer = XSDtoOWLTransformer(uri_encode_method)
    
    # Register class rules
    transformer.register_rule(DetectSimpleTypeRule(), 'class')
    transformer.register_rule(NamedComplexTypeRule(), 'class')
    transformer.register_rule(TargetClassCreationRule(), 'class')
    transformer.register_rule(TopLevelNamedElementRule(), 'class')
    transformer.register_rule(AnonymousComplexTypeRule(), 'class')
    
    # Register property rules
    transformer.register_rule(SimpleTypePropertyRule(), 'property')
    transformer.register_rule(InlineSimpleTypePropertyRule(), 'property')
    transformer.register_rule(ComplexTypeReferenceRule(), 'property')
    transformer.register_rule(NumericTypePropertyRule(), 'property')
    transformer.register_rule(TopLevelSimpleElementRule(), 'property')
    transformer.register_rule(ElementReferenceRule(), 'property')
    transformer.register_rule(ChildElementPropertyRule(), 'property')
    transformer.register_rule(ComplexElementPropertyRule(), 'property')
    
    # Register enum rules
    transformer.register_rule(EnhancedNamedEnumTypeRule(), 'enum')
    transformer.register_rule(EnhancedAnonymousEnumTypeRule(), 'enum')
    
    # Register relationship rules
    transformer.register_rule(SandwichElementPropertyRule(), 'relationship')
    transformer.register_rule(ReferenceTrackingRule(), 'relationship')
    transformer.register_rule(ReferencedElementDomainRule(), 'relationship')
    
    # Register cleanup rules
    transformer.register_rule(DomainFixerRule(), 'cleanup')
    transformer.register_rule(PropertyTypeFixerRule(), 'cleanup')
    
    return transformer


def create_taf_cat_transformer(uri_encode_method: str = "underscore") -> XSDtoOWLTransformer:
    """
    Create a transformer specifically configured for TAF CAT transformation.
    
    Args:
        uri_encode_method: Method to encode URIs with spaces
        
    Returns:
        A configured XSDtoOWLTransformer
    """
    # Start with default transformer
    transformer = create_default_transformer(uri_encode_method)
    
    # Import and register ontology rules
    from xsd_to_owl.rules.ontology_rules import (
        OntologyHeaderRule,
        OntologyAnnotationRule
    )
    
    # Register ontology rules
    transformer.register_rule(OntologyHeaderRule(), 'class')  # Run in class phase
    transformer.register_rule(OntologyAnnotationRule(), 'cleanup')  # Run in cleanup phase
    
    # Add any other TAF CAT specific rules or configurations here
    
    # Debug rules can be added here if needed
    
    return transformer
