# xsd_to_owl/core/pipeline.py
"""
Transformation pipeline for XSD to OWL transformation.
Provides a structured approach to applying rules in phases.
"""

from typing import List, Optional, Any, Dict, Set
from lxml import etree

from xsd_to_owl.utils import logging


class TransformationPhase:
    """
    Base class for transformation phases.
    A phase is a collection of rules that are applied in a specific order.
    """
    
    def __init__(self, name: str, description: str, rules: Optional[List[Any]] = None):
        """
        Initialize a new transformation phase.
        
        Args:
            name: The name of the phase
            description: A description of what the phase does
            rules: The rules to apply in this phase
        """
        self.name = name
        self.description = description
        self.rules = rules or []
        
        # Track processed elements to avoid duplicates
        self._processed_elements: Set[bytes] = set()
    
    def add_rule(self, rule: Any) -> None:
        """
        Add a rule to this phase.
        
        Args:
            rule: The rule to add
        """
        self.rules.append(rule)
    
    def is_processed(self, element: etree._Element) -> bool:
        """
        Check if an element has been processed by this phase.
        
        Args:
            element: The element to check
            
        Returns:
            True if the element has been processed
        """
        element_id = etree.tostring(element)
        return element_id in self._processed_elements
    
    def mark_processed(self, element: etree._Element) -> None:
        """
        Mark an element as processed by this phase.
        
        Args:
            element: The element to mark
        """
        element_id = etree.tostring(element)
        self._processed_elements.add(element_id)
    
    def execute(self, xsd_root: etree._Element, context: Any) -> None:
        """
        Execute this phase on the XSD root.
        
        Args:
            xsd_root: The root element of the XSD
            context: The transformation context
        """
        logging.info(f"Executing phase: {self.name}")
        logging.debug(f"Phase description: {self.description}")
        
        # Sort rules by priority (higher priority first)
        sorted_rules = sorted(self.rules, key=lambda r: getattr(r, 'priority', 0), reverse=True)
        
        # Process all elements with all rules
        self._process_element_tree(xsd_root, sorted_rules, context)
        
        logging.info(f"Completed phase: {self.name}")
    
    def _process_element_tree(self, element: etree._Element, rules: List[Any], context: Any) -> None:
        """
        Process an element and its children with the given rules.
        
        Args:
            element: The element to process
            rules: The rules to apply
            context: The transformation context
        """
        # Process this element
        self._process_element(element, rules, context)
        
        # Process children
        for child in element:
            self._process_element_tree(child, rules, context)
    
    def _process_element(self, element: etree._Element, rules: List[Any], context: Any) -> None:
        """
        Process a single element with the given rules.
        
        Args:
            element: The element to process
            rules: The rules to apply
            context: The transformation context
        """
        # Skip if already processed by this phase
        if self.is_processed(element):
            return
        
        # Try to apply each rule
        for rule in rules:
            if rule.matches(element, context):
                logging.debug(f"Rule {rule.rule_id} matched element {element.tag}")
                rule.transform(element, context)
                self.mark_processed(element)
                break


class ClassCreationPhase(TransformationPhase):
    """Phase for creating OWL classes from XSD types."""
    
    def __init__(self, rules: Optional[List[Any]] = None):
        super().__init__(
            name="Class Creation",
            description="Create OWL classes from XSD complex types and elements",
            rules=rules
        )


class PropertyCreationPhase(TransformationPhase):
    """Phase for creating OWL properties from XSD elements."""
    
    def __init__(self, rules: Optional[List[Any]] = None):
        super().__init__(
            name="Property Creation",
            description="Create OWL properties from XSD elements and attributes",
            rules=rules
        )


class EnumerationPhase(TransformationPhase):
    """Phase for creating SKOS concept schemes from XSD enumerations."""
    
    def __init__(self, rules: Optional[List[Any]] = None):
        super().__init__(
            name="Enumeration Creation",
            description="Create SKOS concept schemes from XSD enumerations",
            rules=rules
        )


class RelationshipPhase(TransformationPhase):
    """Phase for creating relationships between OWL classes and properties."""
    
    def __init__(self, rules: Optional[List[Any]] = None):
        super().__init__(
            name="Relationship Creation",
            description="Create relationships between OWL classes and properties",
            rules=rules
        )


class CleanupPhase(TransformationPhase):
    """Phase for cleaning up the ontology after transformation."""
    
    def __init__(self, rules: Optional[List[Any]] = None):
        super().__init__(
            name="Cleanup",
            description="Clean up the ontology after transformation",
            rules=rules
        )


class TransformationPipeline:
    """
    Manages the transformation pipeline with explicit phases.
    Coordinates the execution of phases in order.
    """
    
    def __init__(self):
        """Initialize a new transformation pipeline with default phases."""
        self.phases: List[TransformationPhase] = [
            ClassCreationPhase(),
            PropertyCreationPhase(),
            EnumerationPhase(),
            RelationshipPhase(),
            CleanupPhase()
        ]
    
    def add_phase(self, phase: TransformationPhase, index: Optional[int] = None) -> None:
        """
        Add a phase to the pipeline.
        
        Args:
            phase: The phase to add
            index: The index at which to insert the phase (None for append)
        """
        if index is None:
            self.phases.append(phase)
        else:
            self.phases.insert(index, phase)
    
    def add_rule_to_phase(self, rule: Any, phase_index: int) -> None:
        """
        Add a rule to a specific phase.
        
        Args:
            rule: The rule to add
            phase_index: The index of the phase to add the rule to
        """
        if 0 <= phase_index < len(self.phases):
            self.phases[phase_index].add_rule(rule)
    
    def execute(self, xsd_root: etree._Element, context: Any) -> None:
        """
        Execute the transformation pipeline.
        
        Args:
            xsd_root: The root element of the XSD
            context: The transformation context
        """
        logging.info("Starting transformation pipeline")
        
        # Execute each phase in order
        for phase in self.phases:
            phase.execute(xsd_root, context)
        
        logging.info("Transformation pipeline complete")