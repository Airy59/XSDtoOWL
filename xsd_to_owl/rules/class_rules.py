# xsd_to_owl/rules/class_rules.py
import rdflib

from ..auxiliary.decorators import check_class_exists, check_already_processed
from ..auxiliary.property_utils import (
    is_datatype_property, determine_datatype_range, find_referenced_element,
    create_datatype_property, create_object_property, property_exists, get_registered_property,
    enhance_existing_property, get_property_uri_for_name, register_property
)
from ..auxiliary.uri_utils import lower_case_initial
from ..auxiliary.xsd_parsers import get_documentation
from ..core.visitor import XSDVisitor

# Define XML Schema namespace constant
XS_NS = "{http://www.w3.org/2001/XMLSchema}"


class DetectSimpleTypeRule(XSDVisitor):
    """
    Rule to detect named simple types (even when defined as complex types with restrictions)
    and prevent them from being turned into classes.
    This rule doesn't create anything, it just marks these types as processed
    so other rules don't handle them.
    """

    @property
    def rule_id(self):
        return "detect_simple_type"

    @property
    def description(self):
        return "Detect simple types and prevent them from becoming classes"

    # Very high priority to run before class creation rules
    @property
    def priority(self):
        return 300

    @check_already_processed
    def matches(self, element, context):
        """Match any named type that should be treated as a simple type."""
        # Skip if not a type definition
        if element.tag not in [f"{XS_NS}simpleType", f"{XS_NS}complexType"]:
            return False

        # Must have a name
        if not element.get('name'):
            return False

        # If it's already explicitly a simpleType, match it
        if element.tag == f"{XS_NS}simpleType":
            return True

        # For complexType, we need to determine if it's actually a simple type with restrictions
        # This is the case if it has a simpleContent element
        if element.find(f".//{XS_NS}simpleContent") is not None:
            return True

        # Also match if it has a restriction directly
        if element.find(f".//{XS_NS}restriction") is not None:
            return True

        return False

    def transform(self, element, context):
        """
        Don't actually create anything, just mark these types as processed
        to prevent them from being turned into classes.
        """
        name = element.get('name')
        print(f"Found simple type: {name} - preventing class creation")

        # Mark as processed for class creation rules
        context.mark_processed(element, "named_complex_type")
        context.mark_processed(element, "named_simple_type")

        # Also mark as processed for this rule to avoid repeated processing
        context.mark_processed(element, self.rule_id)

        return None


class NamedComplexTypeRule(XSDVisitor):
    """
    Rule: xs:complexType[@name] (named) -> owl:Class with URI base:name
    """

    @property
    def rule_id(self):
        return "named_complex_type"

    @property
    def description(self):
        return "Transform named complex types to OWL classes"

    @check_class_exists
    @check_already_processed
    def matches(self, element, context):
        # Basic structure check
        if element.tag != f"{XS_NS}complexType" or element.get('name') is None:
            return False

        # Don't match numeric types
        name = element.get('name')
        if name.startswith('Numeric'):
            print(f"Skipping numeric type in NamedComplexTypeRule: {name}")
            return False

        # Don't match types with numeric pattern (e.g. Numeric3-3)
        import re
        if re.match(r'^Numeric\d+(-\d+)?$', name):
            print(f"Skipping numeric pattern type in NamedComplexTypeRule: {name}")
            return False

        return True

    def transform(self, element, context):
        name = element.get('name')
        class_uri = context.get_safe_uri(context.base_uri, name)

        # Create owl:Class
        context.graph.add((class_uri, context.RDF.type, context.OWL.Class))
        context.graph.add((class_uri, context.RDFS.label, rdflib.Literal(name)))

        # Add documentation if available
        if doc := get_documentation(element):
            context.graph.add((class_uri, context.SKOS.definition, rdflib.Literal(doc)))

        # Mark as processed to avoid conflicts
        context.mark_processed(element, self.rule_id)

        return class_uri


class TargetClassCreationRule(XSDVisitor):
    """
    Rule to ensure that specific classes exist before property creation.
    This rule creates classes that are needed as property targets but might not
    be directly defined in the schema.
    """

    @property
    def rule_id(self):
        return "target_class_creation"

    @property
    def description(self):
        return "Create specific target classes needed for properties"

    @property
    def priority(self):
        return 200  # Higher priority to run before property rules

    def matches(self, element, context):
        # Match elements that need to be created as classes
        if element.tag != f"{XS_NS}element":
            return False

        name = element.get('name')
        ref = element.get('ref')

        # List of elements that need to be created as classes
        target_classes = ["AdministrativeDataSet"]

        if name in target_classes or ref in target_classes:
            target_name = name or ref
            target_uri = context.get_safe_uri(context.base_uri, target_name)

            # Only match if the class doesn't already exist
            if (target_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                print(f"\nEnsuring class exists: {target_name}")
                return True

        return False

    def transform(self, element, context):
        target_name = element.get('name') or element.get('ref')
        target_uri = context.get_safe_uri(context.base_uri, target_name)

        print(f"Creating class: {target_name}")

        # Create the class
        context.graph.add((target_uri, context.RDF.type, context.OWL.Class))
        context.graph.add((target_uri, context.RDFS.label, rdflib.Literal(target_name)))

        # Add documentation if available
        doc = get_documentation(element)
        if doc:
            context.graph.add((target_uri, context.SKOS.definition, rdflib.Literal(doc)))
        else:
            context.graph.add((target_uri, context.RDFS.comment,
                               rdflib.Literal(f"Class for {target_name}")))

        # Mark as processed
        context.mark_processed(element, self.rule_id)

        return target_uri


class TopLevelNamedElementRule(XSDVisitor):
    """
    Rule: xs:element[@name][@type] (top-level, named) -> owl:Class with URI base:name
    """

    @property
    def rule_id(self):
        return "top_level_named_element"

    @property
    def description(self):
        return "Transform top-level named elements to OWL classes or, in some cases, to (data) properties with unspecified domains."

    @check_class_exists
    @check_already_processed
    def matches(self, element, context):
        # Check if it's a named element at the top level
        return (element.tag == f"{XS_NS}element" and
                element.get('name') is not None and
                element.get('type') is not None and
                context.get_parent_element() is not None and
                context.get_parent_element().tag == f"{XS_NS}schema")

    def transform(self, element, context):
        name = element.get('name')
        property_name = lower_case_initial(name)

        # Check if this might be a property based on its type
        type_attr = element.get('type')
        numeric_type = type_attr and (type_attr.startswith('Numeric') or ':' in type_attr)

        # Get a consistently named property URI
        property_uri = context.get_property_uri(property_name)

        # If we already have a property with this name registered
        if property_uri:
            print(f"Found existing property for {property_name}, enhancing it")

            # Check if it already has a definition
            has_def = False
            for _, _, _ in context.graph.triples((property_uri, context.SKOS.definition, None)):
                has_def = True
                break

            # Add definition if missing and available in this element
            if not has_def:
                doc = get_documentation(element)
                if doc:
                    context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc, lang="en")))
                    print(f"  Added documentation to existing property: {property_name}")

            # Mark as processed
            context.mark_processed(element, self.rule_id)
            return property_uri

        # This could be a property based on its type, create it as such
        elif numeric_type or name in ["AirBrakedMass", "AirBrakedMassLoaded"]:  # Special case matches
            property_uri = context.get_safe_uri(context.base_uri, property_name, is_property=True)

            # Create a datatype property
            context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
            context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(property_name)))

            # Determine the range
            if type_attr and type_attr.startswith('Numeric'):
                range_uri = context.XSD.decimal
            elif type_attr and ':' in type_attr:
                range_uri = context.get_type_reference(type_attr)
            else:
                range_uri = context.XSD.string

            context.graph.add((property_uri, context.RDFS.range, range_uri))

            # Add documentation if available
            doc = get_documentation(element)
            if doc:
                context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc, lang="en")))

            # Mark as processed
            context.mark_processed(element, self.rule_id)
            print(f"Created datatype property from top-level element: {property_name}")
            return property_uri

        # Otherwise, treat as a normal class
        class_uri = context.get_safe_uri(context.base_uri, name)

        # Create owl:Class
        context.graph.add((class_uri, context.RDF.type, context.OWL.Class))
        context.graph.add((class_uri, context.RDFS.label, rdflib.Literal(name)))

        # Add documentation if available
        if doc := get_documentation(element):
            context.graph.add((class_uri, context.SKOS.definition, rdflib.Literal(doc)))

        # Mark as processed
        context.mark_processed(element, self.rule_id)
        return class_uri


class AnonymousComplexTypeRule(XSDVisitor):
    """
    Rule: xs:element/xs:complexType (anonymous complex type) ->
          owl:Class + properties for all child elements
    """

    @property
    def rule_id(self):
        return "anonymous_complex_type"

    @property
    def description(self):
        return "Transform anonymous complex types to classes"

    @check_already_processed
    def matches(self, element, context):
        # Match element with a complexType child but no type attribute
        if element.tag != f"{XS_NS}element":
            return False

        if element.get('type') is not None:
            return False

        # Must have a name
        if element.get('name') is None:
            return False

        # Must have a complexType child
        for child in element:
            if child.tag == f"{XS_NS}complexType":
                return True

        return False

    def transform(self, element, context):
        name = element.get('name')
        class_uri = context.get_safe_uri(context.base_uri, name)

        # Create the class
        context.graph.add((class_uri, context.RDF.type, context.OWL.Class))
        context.graph.add((class_uri, context.RDFS.label, rdflib.Literal(name)))

        # Process complex type children
        for child in element:
            if child.tag == f"{XS_NS}complexType":
                # Mark children for property creation
                self._mark_children_for_processing(child, name, class_uri, context)

                # This is key: Create a special flag for elements that have both
                # a parent (are properties) and children (are classes)
                self._mark_sandwich_elements(child, name, class_uri, context)

        # Mark this element as processed
        context.mark_processed(element, self.rule_id)

        return class_uri

    @staticmethod
    def _mark_sandwich_elements(complex_type, parent_name, parent_uri, context):
        """Mark elements that are both classes and property targets."""
        # Find sequence
        sequence = complex_type.find(f"{XS_NS}sequence")
        if sequence is None:
            sequence = complex_type.find(f".//{XS_NS}sequence")
            if sequence is None:
                return

        # Find elements that have complex types themselves
        for child in sequence.findall(f"{XS_NS}element"):
            child_name = child.get('name')

            # Check if this child has a complex type
            has_complex_type = False

            # Check for type attribute first
            child_type = child.get('type')
            if child_type and 'simple' not in child_type.lower():
                has_complex_type = True

            # Check for complex type child element
            for grand_child in child:
                if grand_child.tag == f"{XS_NS}complexType":
                    has_complex_type = True
                    break

            if has_complex_type:
                # This is a "sandwich" element - mark it with special flag
                current_metadata = context.get_element_metadata(child) or {}
                current_metadata['is_sandwich'] = True
                current_metadata['parent_name'] = parent_name
                current_metadata['parent_uri'] = parent_uri
                context.add_element_metadata(child, current_metadata)

    @staticmethod
    def _mark_children_for_processing(complex_type, parent_name, parent_uri, context):
        """
        Mark child elements for processing by the rule system.
        This adds parent context to each child element for later processing.
        """
        # Find all child elements
        print(f"DEBUG: Marking children for {parent_name}")

        # First try direct sequence
        sequence = complex_type.find(f"{XS_NS}sequence")

        # If not found directly, try with descendant search
        if sequence is None:
            sequence = complex_type.find(f".//{XS_NS}sequence")
            if sequence is None:
                print(f"DEBUG: No sequence found in complex type for {parent_name}")
                return

        # Count children for debugging
        children_count = 0

        # Instead of using xpath, use findall with the namespace
        for child in sequence.findall(f"{XS_NS}element"):
            # Get child details for debugging
            child_name = child.get('name')
            child_ref = child.get('ref')
            child_type = child.get('type')

            print(f"DEBUG: Found child element: {child_name or child_ref} (type: {child_type})")

            # Store parent information on the element for later use
            context.add_element_metadata(child, {
                'parent_name': parent_name,
                'parent_uri': parent_uri
            })

            print(f"DEBUG: Marked child {child_name or child_ref} with parent {parent_name}")
            children_count += 1

        print(f"DEBUG: Total children marked for {parent_name}: {children_count}")
