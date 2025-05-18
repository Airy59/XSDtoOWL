# xsd_to_owl/core/__init__.py
"""
Core components for the XSD to OWL transformation framework.
"""

from .visitor import XSDVisitor
from .registry import RuleRegistry
from .context import TransformationContext

__all__ = [
    'XSDVisitor',
    'RuleRegistry',
    'TransformationContext'
]