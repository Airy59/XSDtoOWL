# xsd_to_owl/utils/logging.py
"""
Centralized logging for the XSD to OWL transformation process.
Provides consistent logging across all components.
"""

import logging
import sys
from typing import Optional, Any, Dict

# Define log levels with more descriptive names
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR

# Global logger instance
_logger = None


def get_logger(name: str = "xsd_to_owl") -> logging.Logger:
    """
    Get or create a logger with the given name.
    
    Args:
        name: The name of the logger
        
    Returns:
        A configured logger instance
    """
    global _logger
    
    if _logger is None:
        # Create and configure the logger
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)  # Default level
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        _logger.addHandler(console_handler)
    
    return _logger


def set_level(level: int) -> None:
    """
    Set the logging level.
    
    Args:
        level: The logging level (e.g., DEBUG, INFO, WARNING, ERROR)
    """
    logger = get_logger()
    logger.setLevel(level)
    
    # Also update handlers
    for handler in logger.handlers:
        handler.setLevel(level)


def debug(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a debug message."""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log an info message."""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a warning message."""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log an error message."""
    get_logger().error(msg, *args, **kwargs)


def log_rule_application(rule_id: str, element_tag: str, element_name: Optional[str] = None, 
                         success: bool = True) -> None:
    """
    Log the application of a rule to an element.
    
    Args:
        rule_id: The ID of the rule
        element_tag: The tag of the element
        element_name: The name attribute of the element, if available
        success: Whether the rule was successfully applied
    """
    name_info = f" '{element_name}'" if element_name else ""
    
    if success:
        debug(f"Applied rule '{rule_id}' to {element_tag}{name_info}")
    else:
        debug(f"Rule '{rule_id}' did not match {element_tag}{name_info}")


def log_transformation_start(xsd_file: str, base_uri: str) -> None:
    """
    Log the start of a transformation.
    
    Args:
        xsd_file: The path to the XSD file
        base_uri: The base URI for the ontology
    """
    info(f"Starting transformation of '{xsd_file}' with base URI '{base_uri}'")


def log_transformation_complete(triple_count: int, stats: Dict[str, int]) -> None:
    """
    Log the completion of a transformation.
    
    Args:
        triple_count: The total number of triples in the graph
        stats: Statistics about the generated ontology
    """
    info(f"Transformation complete. Generated {triple_count} triples.")
    info(f"Statistics: {stats}")