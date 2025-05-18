# xsd_to_owl/core/visitor.py
from abc import ABC, abstractmethod


class XSDVisitor(ABC):
    """
    Base visitor interface for XSD to OWL transformation rules.
    Each concrete visitor implements a specific transformation rule.
    """

    @property
    @abstractmethod
    def rule_id(self):
        """Unique identifier for the rule."""
        pass

    @property
    @abstractmethod
    def description(self):
        """Human-readable description of the rule."""
        pass

    @property
    def priority(self):
        """
        Priority of this rule. Higher values indicate higher priority.
        Default is 100. Override in subclasses as needed.
        """
        return 100

    @abstractmethod
    def matches(self, element, context):
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
    def transform(self, element, context):
        """
        Transforms the element according to the rule.

        Args:
            element: The XSD element to transform
            context: The transformation context

        Returns:
            The URI of the created resource or None
        """
        pass
