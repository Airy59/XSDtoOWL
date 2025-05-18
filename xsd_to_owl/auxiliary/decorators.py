# xsd_to_owl/auxiliary/decorators.py
"""
Decorators for XSD to OWL transformation rules.
Provides common functionality for rule matching and execution.
"""

import functools
from typing import Callable, Any

from xsd_to_owl.utils import logging


def check_class_exists(matches_method: Callable) -> Callable:
    """
    Decorator that checks if a class already exists before matching.
    
    Args:
        matches_method: The method to decorate
        
    Returns:
        Decorated method
    """
    @functools.wraps(matches_method)
    def wrapper(self, element, context):
        # Only check named elements
        if not hasattr(element, 'get') or not element.get('name'):
            return matches_method(self, element, context)
        
        name = element.get('name')
        class_uri = context.uri_manager.get_class_uri(name)
        
        if (class_uri, context.RDF.type, context.OWL.Class) in context.graph:
            logging.debug(f"Class {name} already exists - skipping creation")
            return False
        
        return matches_method(self, element, context)
    return wrapper


def check_property_exists(matches_method: Callable) -> Callable:
    """
    Decorator that checks if a property already exists before matching.
    
    Args:
        matches_method: The method to decorate
        
    Returns:
        Decorated method
    """
    @functools.wraps(matches_method)
    def wrapper(self, element, context):
        # Only check named elements
        if not hasattr(element, 'get') or not element.get('name'):
            return matches_method(self, element, context)
        
        name = element.get('name')
        property_name = context.uri_manager._lower_case_initial(name)
        
        # Check if property already exists in registry
        existing_uri = context.get_property_uri(property_name)
        if existing_uri:
            if ((existing_uri, context.RDF.type, context.OWL.DatatypeProperty) in context.graph or
                    (existing_uri, context.RDF.type, context.OWL.ObjectProperty) in context.graph):
                logging.debug(f"Property {property_name} already exists - skipping creation")
                return False
        
        # If not in registry, check if it exists in the graph
        property_uri = context.uri_manager.get_property_uri(name, is_datatype=True)
        if ((property_uri, context.RDF.type, context.OWL.DatatypeProperty) in context.graph or
                (property_uri, context.RDF.type, context.OWL.ObjectProperty) in context.graph):
            logging.debug(f"Property {property_name} already exists - skipping creation")
            return False
        
        return matches_method(self, element, context)
    return wrapper


def check_already_processed(func: Callable) -> Callable:
    """
    Decorator for matches() methods that checks if an element has already
    been processed by this specific rule before performing the actual matching.
    
    This implements proper visitor pattern behavior by allowing multiple rules to
    process the same element, while ensuring that each rule only processes an element once.
    
    Args:
        func: The method to decorate
        
    Returns:
        Decorated method
    """
    @functools.wraps(func)
    def wrapper(self, element, context):
        # First check if this specific rule has already processed this element
        if context.is_processed(element, self.rule_id):
            return False
        
        # If not processed by this rule, proceed with the actual matching logic
        return func(self, element, context)
    
    return wrapper


def log_execution(func: Callable) -> Callable:
    """
    Decorator that logs the execution of a method.
    
    Args:
        func: The method to decorate
        
    Returns:
        Decorated method
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        logging.debug(f"Executing {self.__class__.__name__}.{func.__name__}")
        result = func(self, *args, **kwargs)
        logging.debug(f"Completed {self.__class__.__name__}.{func.__name__}")
        return result
    
    return wrapper
