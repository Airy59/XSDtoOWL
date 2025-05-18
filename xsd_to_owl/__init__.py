"""
XSD to OWL Transformation Framework

This package provides tools for transforming XML Schema Definition (XSD) documents
into Web Ontology Language (OWL) and Simple Knowledge Organization System (SKOS) ontologies.
"""

# Import the main transformer class and factory functions
from xsd_to_owl.transform import (
    XSDtoOWLTransformer,
    create_default_transformer,
    create_taf_cat_transformer
)

# Import core components
from xsd_to_owl.core.context import TransformationContext
from xsd_to_owl.core.pipeline import (
    TransformationPipeline,
    ClassCreationPhase,
    PropertyCreationPhase,
    EnumerationPhase,
    RelationshipPhase,
    CleanupPhase
)

# Import base rule classes
from xsd_to_owl.rules.base import (
    BaseRule,
    BaseClassRule,
    BasePropertyRule,
    BaseEnumRule
)

# Import utility modules
from xsd_to_owl.utils import logging
from xsd_to_owl.utils.uri_manager import URIManager

# Import configuration
from xsd_to_owl.config.special_cases import (
    is_forced_datatype_property,
    is_forced_object_property,
    is_datatype_property_type,
    is_forced_class_type,
    is_forced_class_element
)

# Version information
__version__ = "0.2.0"
__author__ = "CDM-GCU Team"

# Define what's available when using "from xsd_to_owl import *"
__all__ = [
    # Main transformer
    'XSDtoOWLTransformer',
    'create_default_transformer',
    'create_taf_cat_transformer',
    
    # Core components
    'TransformationContext',
    'TransformationPipeline',
    'ClassCreationPhase',
    'PropertyCreationPhase',
    'EnumerationPhase',
    'RelationshipPhase',
    'CleanupPhase',
    
    # Base rules
    'BaseRule',
    'BaseClassRule',
    'BasePropertyRule',
    'BaseEnumRule',
    
    # Utilities
    'logging',
    'URIManager',
    
    # Configuration helpers
    'is_forced_datatype_property',
    'is_forced_object_property',
    'is_datatype_property_type',
    'is_forced_class_type',
    'is_forced_class_element'
]
