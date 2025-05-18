# xsd_to_owl/rules/enum_rules.py
import re

import rdflib
from rdflib import Literal

from ..auxiliary.decorators import check_already_processed
from ..core.visitor import XSDVisitor

# Define XML Schema namespace constant
XS_NS = "{http://www.w3.org/2001/XMLSchema}"


class NamedEnumTypeRule(XSDVisitor):
    """
    Rule: xs:simpleType[@name][xs:restriction/xs:enumeration] (named enum type) ->
          skos:ConceptScheme with URI base:name
          skos:Concept for each @value, with URI base:name_value
    """

    @property
    def rule_id(self):
        return "named_enum_type"

    @property
    def description(self):
        return "Transform named enumeration types to SKOS concept schemes"

    @check_already_processed
    def matches(self, element, context):
        # Match named simple types with enumeration restrictions
        if element.tag != f"{XS_NS}simpleType" or element.get('name') is None:
            return False

        # Check for restriction with enumeration
        for child in element:
            if child.tag == f"{XS_NS}restriction":
                for grandchild in child:
                    if grandchild.tag == f"{XS_NS}enumeration":
                        return True

        return False

    def transform(self, element, context):
        name = element.get('name')
        scheme_uri = context.get_safe_uri(context.base_uri, name)

        # Create ConceptScheme
        context.graph.add((scheme_uri, context.RDF.type, context.SKOS.ConceptScheme))

        # Add label if available
        from xsd_to_owl.auxiliary.xsd_parsers import get_documentation
        scheme_label = get_documentation(element)
        if scheme_label:
            context.graph.add((scheme_uri, context.RDFS.label, rdflib.Literal(scheme_label)))

        # Find restriction and process enumerations
        for child in element:
            if child.tag == f"{XS_NS}restriction":
                self._process_enumerations(child, scheme_uri, name, context)

        # Mark as processed
        context.mark_processed(element, self.rule_id)

        return scheme_uri

    def _process_enumerations(self, restriction_element, scheme_uri, scheme_name, context):
        """Process enumeration values in a restriction."""
        for enum in restriction_element:
            if enum.tag == f"{XS_NS}enumeration":
                value = enum.get('value')
                if value:
                    # Create concept URI
                    concept_uri = context.get_safe_uri(context.base_uri, f"{scheme_name}_{value}")

                    # Create Concept
                    context.graph.add((concept_uri, context.RDF.type, context.SKOS.Concept))
                    context.graph.add((concept_uri, context.SKOS.inScheme, scheme_uri))

                    # Add prefLabel
                    context.graph.add((concept_uri, context.SKOS.prefLabel, rdflib.Literal(value)))

                    # Add definition if available
                    from xsd_to_owl.auxiliary.xsd_parsers import get_documentation
                    definition = get_documentation(enum)
                    if definition:
                        context.graph.add((concept_uri, context.SKOS.definition, rdflib.Literal(definition)))




class AnonymousEnumTypeRule(XSDVisitor):
    """
    Rule: xs:element[@name][xs:simpleType/xs:restriction/xs:enumeration] (anonymous enum inline) ->
          skos:ConceptScheme with URI base:ElementName_enum
          skos:Concept for each @value, with URI base:ElementName_enum_value
    """

    @property
    def rule_id(self):
        return "anonymous_enum_type"

    @property
    def description(self):
        return "Transform elements with anonymous enumeration types to SKOS concept schemes"

    @check_already_processed
    def matches(self, element, context):
        # Match elements with name that contain an inline simple type with enumeration
        if element.tag != f"{XS_NS}element" or element.get('name') is None:
            return False

        # Check for inline simpleType with restriction and enumeration
        for child in element:
            if child.tag == f"{XS_NS}simpleType":
                for grandchild in child:
                    if grandchild.tag == f"{XS_NS}restriction":
                        for greatgrandchild in grandchild:
                            if greatgrandchild.tag == f"{XS_NS}enumeration":
                                return True

        return False

    def transform(self, element, context):
        name = element.get('name')
        scheme_uri = context.get_safe_uri(context.base_uri, f"{name}_enum")

        # Create ConceptScheme
        context.graph.add((scheme_uri, context.RDF.type, context.SKOS.ConceptScheme))

        # Add label
        context.graph.add((scheme_uri, context.RDFS.label,
                           rdflib.Literal(f"Enumeration for {name}")))

        # Find simpleType, restriction and process enumerations
        for child in element:
            if child.tag == f"{XS_NS}simpleType":
                for grandchild in child:
                    if grandchild.tag == f"{XS_NS}restriction":
                        self._process_enumerations(grandchild, scheme_uri, f"{name}_enum", context)

        # Mark as processed
        context.mark_processed(element, self.rule_id)

        return scheme_uri

    def _process_enumerations(self, restriction_element, scheme_uri, scheme_prefix, context):
        """Process enumeration values in a restriction."""
        for enum in restriction_element:
            if enum.tag == f"{XS_NS}enumeration":
                value = enum.get('value')
                if value:
                    # Create concept URI
                    concept_uri = context.get_safe_uri(context.base_uri, f"{scheme_prefix}_{value}")

                    # Create Concept
                    context.graph.add((concept_uri, context.RDF.type, context.SKOS.Concept))
                    context.graph.add((concept_uri, context.SKOS.inScheme, scheme_uri))

                    # Add prefLabel
                    context.graph.add((concept_uri, context.SKOS.prefLabel, rdflib.Literal(value)))

                    # Add definition if available
                    from xsd_to_owl.auxiliary.xsd_parsers import get_documentation
                    definition = get_documentation(enum)
                    if definition:
                        context.graph.add((concept_uri, context.SKOS.definition, rdflib.Literal(definition)))




# Add to enum_rules.py


class EnhancedEnumRule:
    """Base class for enhanced enumeration rules with definition extraction"""


    def _extract_definition_from_annotation(self, element, value):
        """
        Extract a definition for a specific enumeration value from an annotation.

        Args:
            element: The XML element containing the annotation
            value: The enumeration value to find a definition for

        Returns:
            str or None: The extracted definition, or None if not found
        """
        # Find the annotation element
        annotation_element = element.find('./{http://www.w3.org/2001/XMLSchema}annotation')
        if annotation_element is None:
            return None

        # Extract documentation text
        doc_elements = annotation_element.findall('.//{http://www.w3.org/2001/XMLSchema}documentation')
        if not doc_elements:
            return None

        # Combine all documentation text
        annotation_text = ' '.join(elem.text for elem in doc_elements if elem.text)
        if not annotation_text:
            return None

        # Clean and normalize the annotation text
        annotation_text = annotation_text.replace('\n', ' ').replace('\t', ' ')
        annotation_text = ' '.join(annotation_text.split())

        # Try various patterns to extract the definition
        patterns = [
            # "1 = Automatic" pattern
            rf'{re.escape(value)}\s*=\s*([^=0-9]+)',
            # "1: Automatic" pattern
            rf'{re.escape(value)}\s*:\s*([^:0-9]+)',
            # "1 - Automatic" pattern
            rf'{re.escape(value)}\s*-\s*([^-0-9]+)',
            # Simple "1 Automatic" pattern (value followed by description)
            rf'{re.escape(value)}\s+([^=:0-9][^0-9]+)'
        ]

        # Try each pattern
        for pattern in patterns:
            matches = re.findall(pattern, annotation_text)
            if matches:
                definition = matches[0].strip()
                return definition

        # Try a different approach: extract text between this value and the next value/end
        pos = annotation_text.find(value)
        if pos >= 0:
            # Extract from after this value to the end or next enumeration
            start_pos = pos + len(value)
            next_value_pos = -1

            # Look for other enumeration values that might follow
            for enum_val in self._extract_all_enum_values(element):
                if enum_val != value:
                    val_pos = annotation_text.find(enum_val, start_pos)
                    if val_pos > 0 and (next_value_pos == -1 or val_pos < next_value_pos):
                        next_value_pos = val_pos

            # Extract the text
            if next_value_pos > 0:
                definition = annotation_text[start_pos:next_value_pos].strip()
            else:
                definition = annotation_text[start_pos:].strip()

            # Clean up the definition
            definition = re.sub(r'^[=:,\s-]+', '', definition).strip()
            if definition:
                return definition

        return None

    def _extract_all_enum_values(self, element):
        """Extract all enumeration values from an element"""
        enum_values = []
        for enum_elem in element.findall('.//*[@value]'):
            if enum_elem.tag.endswith('}enumeration'):
                enum_values.append(enum_elem.get('value'))
        return enum_values

    def _add_definitions_to_concepts(self, context, scheme_uri, enum_values, element):
        """
        Add definitions to SKOS concepts based on annotations

        Args:
            context: The transformation context
            scheme_uri: URI of the concept scheme
            enum_values: List of enumeration values
            element: The XML element containing the annotation
        """
        for value in enum_values:
            concept_uri = context.get_concept_uri(scheme_uri, value)

            # Only add definition if the concept exists
            if (concept_uri, context.RDF.type, context.SKOS.Concept) in context.graph:
                definition = self._extract_definition_from_annotation(element, value)
                if definition:
                    context.graph.add((concept_uri, context.RDFS.comment, Literal(definition, lang="en")))
                    print(f"Added definition for concept {value}: {definition}")


# Enhanced versions of the existing enumeration rules

class EnhancedNamedEnumTypeRule(NamedEnumTypeRule, EnhancedEnumRule):
    """Enhanced version of NamedEnumTypeRule that extracts definitions from annotations"""

    def transform(self, element, context):
        # Call the original transform method
        scheme_uri = super().transform(element, context)

        # Get the enumeration values
        enum_values = self._extract_all_enum_values(element)

        # Add definitions to concepts
        self._add_definitions_to_concepts(context, scheme_uri, enum_values, element)

        return scheme_uri


class EnhancedAnonymousEnumTypeRule(AnonymousEnumTypeRule, EnhancedEnumRule):
    """Enhanced version of AnonymousEnumTypeRule that extracts definitions from annotations"""

    def transform(self, element, context):
        # Call the original transform method
        scheme_uri = super().transform(element, context)

        # Get the enumeration values
        enum_values = self._extract_all_enum_values(element)

        # Add definitions to concepts
        self._add_definitions_to_concepts(context, scheme_uri, enum_values, element)

        return scheme_uri
