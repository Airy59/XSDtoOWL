# xsd_to_owl/config/special_cases.py
"""
Configuration for special cases in XSD to OWL transformation.
Defines elements and types that require special handling.
"""

import re
from typing import Dict, Any, List, Set

# Special case elements that should be treated as datatype properties
# regardless of their structure or type
FORCE_DATATYPE_PROPERTIES: Dict[str, Dict[str, Any]] = {
    "airBrakedMassLoaded": {
        "range": "xsd:decimal",
        "comment": "Forced to be a datatype property with decimal range"
    },
    "airBrakedMass": {
        "range": "xsd:decimal",
        "comment": "Forced to be a datatype property with decimal range"
    }
}

# Special case elements that should be treated as object properties
# regardless of their structure or type
FORCE_OBJECT_PROPERTIES: Dict[str, Dict[str, Any]] = {
    "administrativeDataSet": {
        "comment": "Forced to be an object property"
    }
}

# Special case types that should be treated as datatype properties
# when referenced by elements
DATATYPE_PROPERTY_TYPES: List[str] = [
    "Numeric3-3",
    "Numeric1-1",
    "Numeric2-2",
    "Numeric4-4",
    "Numeric5-5",
    "Numeric6-6",
    "Numeric7-7",
    "Numeric8-8",
    "Numeric9-9",
    "Numeric10-10",
    "Numeric11-11",
    "Numeric12-12"
]

# Special case types that should be treated as classes
# even if they might otherwise be treated as simple types
FORCE_CLASS_TYPES: List[str] = [
    "RollingStockDataSet",
    "WagonDataSet"
]

# Special case elements that should be created as classes
# even if they appear in property contexts
FORCE_CLASS_ELEMENTS: List[str] = [
    "AdministrativeDataSet"
]

# Special case elements that should be skipped entirely
# (not processed by any rules)
SKIP_ELEMENTS: List[str] = [
    # Add any elements that should be skipped
]

# Special case types that should be skipped entirely
# (not processed by any rules)
SKIP_TYPES: List[str] = [
    # Add any types that should be skipped
]

# This set is kept for backward compatibility but is no longer used
# Elements with Numeric types are now automatically detected and handled
NEVER_OBJECT_PROPERTIES: Set[str] = set()

def is_forced_datatype_property(element_name: str) -> bool:
    """
    Check if an element should be forced to be a datatype property.
    
    Args:
        element_name: The name of the element
        
    Returns:
        True if the element should be forced to be a datatype property
    """
    return element_name in FORCE_DATATYPE_PROPERTIES or element_name in NEVER_OBJECT_PROPERTIES


def is_forced_object_property(element_name: str) -> bool:
    """
    Check if an element should be forced to be an object property.
    
    Args:
        element_name: The name of the element
        
    Returns:
        True if the element should be forced to be an object property
    """
    return element_name in FORCE_OBJECT_PROPERTIES and element_name not in NEVER_OBJECT_PROPERTIES


def is_datatype_property_type(type_name: str) -> bool:
    """
    Check if a type should be treated as a datatype property.
    
    Args:
        type_name: The name of the type
        
    Returns:
        True if the type should be treated as a datatype property
    """
    # Check for exact matches in the list
    if type_name in DATATYPE_PROPERTY_TYPES:
        return True
    
    # Check for Numeric patterns using regex
    # Match patterns like Numeric1-5, Numeric3, etc.
    if re.match(r'^Numeric\d+(-\d+)?$', type_name):
        return True
    
    return False


def is_forced_class_type(type_name: str) -> bool:
    """
    Check if a type should be forced to be a class.
    
    Args:
        type_name: The name of the type
        
    Returns:
        True if the type should be forced to be a class
    """
    return type_name in FORCE_CLASS_TYPES


def is_forced_class_element(element_name: str) -> bool:
    """
    Check if an element should be forced to be a class.
    
    Args:
        element_name: The name of the element
        
    Returns:
        True if the element should be forced to be a class
    """
    return element_name in FORCE_CLASS_ELEMENTS


def should_skip_element(element_name: str) -> bool:
    """
    Check if an element should be skipped entirely.
    
    Args:
        element_name: The name of the element
        
    Returns:
        True if the element should be skipped
    """
    return element_name in SKIP_ELEMENTS


def should_skip_type(type_name: str) -> bool:
    """
    Check if a type should be skipped entirely.
    
    Args:
        type_name: The name of the type
        
    Returns:
        True if the type should be skipped
    """
    return type_name in SKIP_TYPES


def get_datatype_property_config(element_name: str) -> Dict[str, Any]:
    """
    Get the configuration for a forced datatype property.
    
    Args:
        element_name: The name of the element
        
    Returns:
        Configuration dictionary or empty dict if not found
    """
    return FORCE_DATATYPE_PROPERTIES.get(element_name, {})


def get_object_property_config(element_name: str) -> Dict[str, Any]:
    """
    Get the configuration for a forced object property.
    
    Args:
        element_name: The name of the element
        
    Returns:
        Configuration dictionary or empty dict if not found
    """
    return FORCE_OBJECT_PROPERTIES.get(element_name, {})


def should_never_be_object_property(element_name: str, element_type: str = None) -> bool:
    """
    Check if an element should never be an object property.
    
    This function checks if an element should be treated as a datatype property
    based on its type. Elements with Numeric types should never be object properties.
    
    Args:
        element_name: The name of the element
        element_type: The type of the element (optional)
        
    Returns:
        True if the element should never be an object property
    """
    # If element_type is provided, check if it's a Numeric type
    if element_type:
        # Check if it's a Numeric type using regex
        import re
        if re.match(r'^Numeric\d+(-\d+)?$', element_type):
            return True
    
    # For backward compatibility, still check the NEVER_OBJECT_PROPERTIES set
    # (though it's now empty)
    return element_name in NEVER_OBJECT_PROPERTIES