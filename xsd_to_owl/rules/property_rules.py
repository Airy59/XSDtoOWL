# xsd_to_owl/rules/property_rules.py

import re

import rdflib
from rdflib import BNode

from xsd_to_owl.auxiliary.decorators import check_property_exists, check_already_processed
from xsd_to_owl.auxiliary.uri_utils import lower_case_initial
from xsd_to_owl.core.visitor import XSDVisitor
from xsd_to_owl.utils import logging

# Constants
XS_NS = "{http://www.w3.org/2001/XMLSchema}"

# Dictionary to store element references inside choice elements
# This will be used to set domains for properties that don't have them
CHOICE_ELEMENT_REFS = {}


class SimpleTypePropertyRule(XSDVisitor):
    """
    Rule: xs:element[@name][@type='xs:*'] (simple XSD type) ->
          owl:DatatypeProperty with:
          rdf:about="base:ElementName"
          rdfs:domain = base:ParentTypeName
          rdfs:range = xsd:type
    """

    @property
    def rule_id(self):
        return "simple_type_property"

    @property
    def description(self):
        return "Transform elements with simple XSD types to datatype properties"

    @check_property_exists
    @check_already_processed
    def matches(self, element, context):
        # Basic structural check
        if element.tag != f"{XS_NS}element" or element.get('name') is None or element.get('type') is None:
            return False

        type_name = element.get('type')

        # Special case handling - explicitly identify types that should be datatype properties
        special_cases = ["AirBrakedMassLoaded"]  # Add more as needed
        if type_name in special_cases:
            return True

        # Regular built-in XSD types
        return ':' in type_name

    def transform(self, element, context):
        name = element.get('name')
        type_name = element.get('type')

        # # Get parent element name instead of URI
        # parent_element = element
        # parent_name = None
        # while True:
        #     parent = parent_element.getparent()
        #     if parent is None:
        #         return None  # Can't create property without domain
        #
        #     if parent.tag == f"{XS_NS}complexType" and parent.get('name'):
        #         parent_name = parent.get('name')
        #         break
        #     elif parent.tag == f"{XS_NS}element" and parent.get('name'):
        #         for child in parent:
        #             if child.tag == f"{XS_NS}complexType":
        #                 parent_name = parent.get('name')
        #                 break
        #         if parent_name:
        #             break
        #
        #     parent_element = parent
        #
        # if not parent_name:
        #     return None  # Can't identify parent
        #
        # # Ensure parent class exists
        # parent_uri = ensure_class_exists(parent_name, context, f"domain for property {name}")

        # Create property URI
        property_uri = context.get_safe_uri(context.base_uri, name, is_property=True)

        # Determine range from the XSD type
        range_uri = context.get_type_reference(type_name)

        # Create DatatypeProperty
        context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
        context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(lower_case_initial(name))))

        # context.graph.add((property_uri, context.RDFS.domain, parent_uri))
        set_property_domain(context, property_uri, element)
        context.graph.add((property_uri, context.RDFS.range, range_uri))

        # Add functional property if appropriate
        from xsd_to_owl.auxiliary.xsd_parsers import is_functional, get_documentation
        if is_functional(element):
            context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

        # Add documentation if available
        doc = get_documentation(element)
        if doc:
            context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc)))

        context.mark_processed(element, self.rule_id)

        return property_uri


def find_parent_element(element, context):
    """
    Find the parent complex type or element for an element.
    Returns the URI of the parent class, ensuring it exists in the graph.
    
    This function handles nested anonymous elements and choice elements,
    traversing up the tree until it finds a suitable named parent.
    """
    # Navigate up until we find a suitable parent
    current = element
    last_named_element = None
    
    while True:
        parent = current.getparent()
        if parent is None:
            # If we reached the root without finding a named parent,
            # but we did find a named element earlier, use that
            if last_named_element is not None:
                parent_name = last_named_element.get('name')
                parent_uri = context.get_safe_uri(context.base_uri, parent_name)
                
                # Ensure the class exists
                if (parent_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                    context.graph.add((parent_uri, context.RDF.type, context.OWL.Class))
                    context.graph.add((parent_uri, context.RDFS.label, rdflib.Literal(parent_name)))
                    context.graph.add((parent_uri, context.RDFS.comment,
                                      rdflib.Literal(f"Auto-created by property rule as domain")))
                
                return parent_uri
            return None

        # Check if this is a named element
        if parent.tag == f"{XS_NS}element" and parent.get('name'):
            last_named_element = parent
            
            # If this element has a complex type child, it's a suitable parent
            has_complex_type = False
            for child in parent:
                if child.tag == f"{XS_NS}complexType":
                    has_complex_type = True
                    break
            
            if has_complex_type:
                parent_name = parent.get('name')
                parent_uri = context.get_safe_uri(context.base_uri, parent_name)
                
                # Ensure the class exists
                if (parent_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                    print(f"Warning: find_parent_element needs to create class '{parent_name}' as domain")
                    context.graph.add((parent_uri, context.RDF.type, context.OWL.Class))
                    context.graph.add((parent_uri, context.RDFS.label, rdflib.Literal(parent_name)))
                    context.graph.add((parent_uri, context.RDFS.comment,
                                      rdflib.Literal(f"Auto-created by property rule as domain")))
                
                return parent_uri
        
        # Check if this is a named complex type
        elif parent.tag == f"{XS_NS}complexType" and parent.get('name'):
            parent_name = parent.get('name')
            parent_uri = context.get_safe_uri(context.base_uri, parent_name)
            
            # Ensure the class exists
            if (parent_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                print(f"Warning: find_parent_element needs to create class '{parent_name}' as domain")
                context.graph.add((parent_uri, context.RDF.type, context.OWL.Class))
                context.graph.add((parent_uri, context.RDFS.label, rdflib.Literal(parent_name)))
                context.graph.add((parent_uri, context.RDFS.comment,
                                  rdflib.Literal(f"Auto-created by property rule as domain")))
            
            return parent_uri
        
        # Special handling for choice elements
        elif parent.tag == f"{XS_NS}choice":
            # For choice elements, we need to continue up the tree
            # but also check if we're inside a named element
            choice_parent = parent.getparent()
            if choice_parent is not None and choice_parent.tag == f"{XS_NS}complexType":
                complex_parent = choice_parent.getparent()
                if complex_parent is not None and complex_parent.tag == f"{XS_NS}element" and complex_parent.get('name'):
                    parent_name = complex_parent.get('name')
                    parent_uri = context.get_safe_uri(context.base_uri, parent_name)
                    
                    # Ensure the class exists
                    if (parent_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                        print(f"Warning: find_parent_element needs to create class '{parent_name}' as domain (from choice)")
                        context.graph.add((parent_uri, context.RDF.type, context.OWL.Class))
                        context.graph.add((parent_uri, context.RDFS.label, rdflib.Literal(parent_name)))
                        context.graph.add((parent_uri, context.RDFS.comment,
                                          rdflib.Literal(f"Auto-created by property rule as domain")))
                    
                    return parent_uri
        
        current = parent


def ensure_class_exists(class_name, context, source_info=None):
    """
    Ensure a class with the given name exists in the graph.
    Returns the class URI.
    """
    class_uri = context.get_safe_uri(context.base_uri, class_name)

    # Check if the class already exists
    if (class_uri, context.RDF.type, context.OWL.Class) not in context.graph:
        print(f"Creating class '{class_name}' from {source_info or 'unknown source'}")
        context.graph.add((class_uri, context.RDF.type, context.OWL.Class))
        context.graph.add((class_uri, context.RDFS.label, rdflib.Literal(class_name)))

        if source_info:
            context.graph.add((class_uri, context.RDFS.comment,
                               rdflib.Literal(f"Auto-created: {source_info}")))

    return class_uri


class InlineSimpleTypePropertyRule(XSDVisitor):
    """
    Rule: xs:element[@name][xs:simpleType] (anonymous simple type inline) ->
          owl:DatatypeProperty with:
          rdf:about="base:ElementName"
          rdfs:domain = base:ParentTypeName
          rdfs:range = determined from base type
    """

    @property
    def rule_id(self):
        return "inline_simple_type_property"

    @property
    def description(self):
        return "Transform elements with inline simple types to datatype properties"

    @check_property_exists
    @check_already_processed
    def matches(self, element, context):
        # Must be an element with name
        if element.tag != f"{XS_NS}element" or element.get('name') is None:
            return False

        # Must contain an inline simpleType
        simple_type = element.find(f".//{XS_NS}simpleType")
        if simple_type is None:
            return False

        # And must not contain a complexType
        complex_type = element.find(f".//{XS_NS}complexType")
        return complex_type is None

    def _get_base_type(self, simple_type, context):
        """Determine the base type of a simpleType element."""
        restriction = simple_type.find(f".//{XS_NS}restriction")
        if restriction is not None and restriction.get('base'):
            base_type = restriction.get('base')
            # Handle built-in XSD types and custom types
            if ':' in base_type:
                return context.get_type_reference(base_type)
            else:
                return context.get_safe_uri(context.base_uri, base_type)

        # Default to string if not found
        return context.XSD.string

    def transform(self, element, context):
        name = element.get('name')

        # Create property URI
        property_uri = context.get_safe_uri(context.base_uri, name, is_property=True)

        # Find the simpleType and determine its base type
        simple_type = element.find(f".//{XS_NS}simpleType")
        range_uri = self._get_base_type(simple_type, context)

        # Create DatatypeProperty
        context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
        context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(lower_case_initial(name))))
        set_property_domain(context, property_uri, element)
        context.graph.add((property_uri, context.RDFS.range, range_uri))

        # Add functional property if appropriate
        from xsd_to_owl.auxiliary.xsd_parsers import is_functional, get_documentation
        if is_functional(element):
            context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

        # Add documentation if available
        doc = get_documentation(element)
        if doc:
            context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc)))

        return property_uri


class ComplexTypeReferenceRule(XSDVisitor):
    """
    Rule: xs:element[@name][@type='MyComplexType'] (refers to named complexType) ->
          owl:ObjectProperty with:
          rdf:about="base:ElementName"
          rdfs:domain = base:ParentTypeName
          rdfs:range = base:MyComplexType
    """

    @property
    def rule_id(self):
        return "complex_type_reference"

    @property
    def description(self):
        return "Transform elements referring to complex types to object properties"

    @property
    def priority(self):
        return 50

    @check_property_exists
    @check_already_processed
    def matches(self, element, context):
        # Basic structural check
        if element.tag != f"{XS_NS}element" or element.get('name') is None or element.get('type') is None:
            return False

        # Get element name and type
        name = element.get('name')
        type_name = element.get('type')

        # Import the configuration
        from xsd_to_owl.config.special_cases import should_never_be_object_property
        
        # Skip elements that should never be object properties
        if name and should_never_be_object_property(name, type_name):
            return False
            
        # Skip built-in XSD types and special cases
        if ':' in type_name or type_name.startswith("Numeric") or "Decimal" in type_name:
            return False
            
        # Skip numeric types
        if type_name and (type_name.startswith("Numeric") or "Decimal" in type_name or type_name == "AirBrakedMassLoaded"):
            logging.debug(f"Skipping numeric type: {type_name}")
            return False

        # Only match if the type exists as a complex type in the schema
        schema_root = element.getroottree().getroot()
        complex_type = schema_root.find(f".//xs:complexType[@name='{type_name}']",
                                        namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
        return complex_type is not None

    def _find_parent_type(self, element, context):
        """Find the parent complex type for an element."""
        # Navigate up until we find a complex type
        current = element
        while True:
            parent = current.getparent()
            if parent is None:
                return None

            if parent.tag == f"{XS_NS}complexType" and parent.get('name'):
                # Found named complex type parent
                return context.get_safe_uri(context.base_uri, parent.get('name'))

            elif parent.tag == f"{XS_NS}element" and parent.get('name'):
                # Found parent element with name
                # (this covers the case of anonymous complex types)
                for child in parent:
                    if child.tag == f"{XS_NS}complexType":
                        return context.get_safe_uri(context.base_uri, parent.get('name'))

            current = parent

    def transform(self, element, context):
        name = element.get('name')
        type_name = element.get('type')

        # # Get parent complex type (domain)
        # parent = self._find_parent_type(element, context)
        # if not parent:
        #     # Can't create property without domain
        #     return None

        # Create property URI
        property_uri = context.get_safe_uri(context.base_uri, name, is_property=True)

        # Check if property already exists as a datatype property
        if (property_uri, context.RDF.type, context.OWL.DatatypeProperty) in context.graph:
            logging.debug(f"Property {name} already exists as a datatype property - skipping object property creation")
            return property_uri

        # Reference to the range class
        range_uri = context.get_safe_uri(context.base_uri, type_name)

        # Create ObjectProperty
        context.graph.add((property_uri, context.RDF.type, context.OWL.ObjectProperty))
        context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(lower_case_initial(name))))
        set_property_domain(context, property_uri, element)
        context.graph.add((property_uri, context.RDFS.range, range_uri))

        # Add functional property if appropriate
        from xsd_to_owl.auxiliary.xsd_parsers import is_functional, get_documentation
        if is_functional(element):
            context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

        # Add documentation if available
        doc = get_documentation(element)
        if doc:
            context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc)))

        return property_uri


class NumericTypePropertyRule(XSDVisitor):
    """
    Rule: xs:element[@name][@type='NumericX-Y'] (custom numeric type) ->
          owl:DatatypeProperty with:
          rdf:about="base:ElementName"
          rdfs:domain = base:ParentTypeName
          rdfs:range = xsd:decimal
    """

    @property
    def rule_id(self):
        return "numeric_type_property"

    @property
    def description(self):
        return "Transform elements with Numeric types to decimal datatype properties"

    # Higher priority means this rule runs first
    @property
    def priority(self):
        return 150

    @check_property_exists
    @check_already_processed
    def matches(self, element, context):
        # Match elements with name and type attribute starting with 'Numeric'
        if element.tag != f"{XS_NS}element" or element.get('name') is None:
            return False

        # Import the configuration
        from xsd_to_owl.config.special_cases import should_never_be_object_property, is_forced_datatype_property

        name = element.get('name')
        type_attr = element.get('type')
        if not type_attr:
            return False

        # Special case handling - if it's in our forced datatype properties list
        if name and (is_forced_datatype_property(name) or should_never_be_object_property(name, type_attr)):
            logging.debug(f"NumericTypePropertyRule matched {name} as a forced datatype property")
            return True

        # Check if it's a Numeric type (including more pattern variations)
        is_numeric = (type_attr.startswith('Numeric') or
                      re.match(r'^Numeric\d+(-\d+)?$', type_attr) is not None)

        return is_numeric

    @staticmethod
    def _find_parent_type(element, context):
        """Find the parent complex type for an element."""
        # Navigate up until we find a complex type
        current = element
        while True:
            parent = current.getparent()
            if parent is None:
                return None

            if parent.tag == f"{XS_NS}complexType" and parent.get('name'):
                # Found named complex type parent
                return context.get_safe_uri(context.base_uri, parent.get('name'))

            elif parent.tag == f"{XS_NS}element" and parent.get('name'):
                # Found parent element with name
                # (this covers the case of anonymous complex types)
                for child in parent:
                    if child.tag == f"{XS_NS}complexType":
                        return context.get_safe_uri(context.base_uri, parent.get('name'))

            current = parent

    def transform(self, element, context):
        name = element.get('name')
        type_name = element.get('type')

        # Add debug output for AirBrakedMassLoaded
        if name == "AirBrakedMassLoaded":
            print(f"NumericTypePropertyRule transforming AirBrakedMassLoaded element with type: {type_name}")

        # # Get parent complex type (domain)
        # parent = self._find_parent_type(element, context)
        # if not parent:
        #     # Can't create property without domain
        #     return None

        # Create property URI
        property_uri = context.get_safe_uri(context.base_uri, name, is_property=True)

        # Use xsd:decimal for all Numeric types
        range_uri = context.XSD.decimal

        # Debug print for AirBrakedMassLoaded
        if name == "AirBrakedMassLoaded":
            print(f"DEBUG: Before removing triples for {name}")
            for s, p, o in context.graph.triples((property_uri, None, None)):
                print(f"DEBUG: Found triple: {s} {p} {o}")

        # First, completely remove the property if it exists
        # This ensures we don't have conflicting property types
        context.graph.remove((property_uri, None, None))

        # Debug print for AirBrakedMassLoaded
        if name == "AirBrakedMassLoaded":
            print(f"DEBUG: After removing triples for {name}")
            for s, p, o in context.graph.triples((property_uri, None, None)):
                print(f"DEBUG: Found triple: {s} {p} {o}")

        # Create DatatypeProperty
        context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
        context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(lower_case_initial(name))))
        set_property_domain(context, property_uri, element)
        context.graph.add((property_uri, context.RDFS.range, range_uri))

        # Debug print for AirBrakedMassLoaded
        if name == "AirBrakedMassLoaded":
            print(f"DEBUG: After adding datatype property triples for {name}")
            for s, p, o in context.graph.triples((property_uri, None, None)):
                print(f"DEBUG: Found triple: {s} {p} {o}")

        # Add functional property if appropriate
        from xsd_to_owl.auxiliary.xsd_parsers import is_functional, get_documentation
        if is_functional(element):
            context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

        # Add documentation if available
        doc = get_documentation(element)
        if doc:
            context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc)))

        # Add comment about original type
        comment = f"Original XSD type was {type_name}"
        context.graph.add((property_uri, context.RDFS.comment, rdflib.Literal(comment)))
        
        # Register the property as a datatype property
        from xsd_to_owl.auxiliary.property_utils import register_property
        register_property(lower_case_initial(name), property_uri, is_datatype=True)

        # Mark the element as processed by ALL rules that might otherwise process it
        context.mark_processed(element, self.rule_id)
        context.mark_processed(element, "complex_type_reference")  # Prevent ComplexTypeReferenceRule from processing
        context.mark_processed(element, "simple_type_property")  # Prevent SimpleTypePropertyRule from processing

        # IMPORTANT: Also prevent the Numeric classes themselves from being created
        # Find and mark any simpleType or complexType element with the same name
        numeric_type_name = type_name
        for type_elem in element.getroottree().xpath(
                f"//xs:simpleType[@name='{numeric_type_name}'] | //xs:complexType[@name='{numeric_type_name}']",
                namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'}):
            context.mark_processed(type_elem, "named_complex_type")  # Prevent NamedComplexTypeRule from processing
            context.mark_processed(type_elem, "named_simple_type")  # Prevent any SimpleType rule from processing

        return property_uri


class TopLevelSimpleElementRule(XSDVisitor):
    """
    Rule: Top-level xs:element with simpleType or built-in type reference ->
          owl:DatatypeProperty
    """

    @property
    def rule_id(self):
        return "top_level_simple_element"

    @property
    def description(self):
        return "Transform top-level simple type elements into datatype properties"

    # Set very high priority to ensure this runs first
    @property
    def priority(self):
        return 200  # Higher than any other rule

    @check_property_exists
    @check_already_processed
    def matches(self, element, context):
        # Must be an element with a name
        if element.tag != f"{XS_NS}element" or element.get('name') is None:
            return False

        # Check if it's AirBrakedMass or any other top-level simple element
        name = element.get('name')

        # Debug print
        if name == "AirBrakedMass":
            print(f"Found AirBrakedMass element: {element}")
            parent = element.getparent()
            print(f"Parent tag: {parent.tag if parent is not None else 'None'}")
            type_attr = element.get('type')
            print(f"Type attribute: {type_attr}")
            has_simple_type = element.find(f".//{XS_NS}simpleType") is not None
            print(f"Has simple type: {has_simple_type}")

            # Always match this specific element
            return True

        # Only match direct children of the schema
        parent = element.getparent()
        if parent is None or parent.tag != f"{XS_NS}schema":
            return False

        # Must have a simple type (inline or reference)
        has_simple_type = element.find(f".//{XS_NS}simpleType") is not None
        is_built_in_type = element.get('type') is not None and ':' in element.get('type')
        is_numeric_type = element.get('type') is not None and element.get('type').startswith('Numeric')

        # Exclude complex types
        has_complex_type = element.find(f".//{XS_NS}complexType") is not None

        return (has_simple_type or is_built_in_type or is_numeric_type) and not has_complex_type

    @staticmethod
    def _extract_consolidated_annotation(element, element_ref=None):
        """Extract and consolidate annotations from an element and its reference."""
        annotations = []

        # Process annotations from the main element
        if element is not None:
            annotation_element = element.find(f'.//{XS_NS}annotation')
            if annotation_element is not None:
                doc_elements = annotation_element.findall(f'.//{XS_NS}documentation')
                for doc in doc_elements:
                    if doc.text:
                        annotations.append(doc.text.strip())

        # Process annotations from the element reference
        if element_ref is not None:
            annotation_element = element_ref.find(f'.//{XS_NS}annotation')
            if annotation_element is not None:
                doc_elements = annotation_element.findall(f'.//{XS_NS}documentation')
                for doc in doc_elements:
                    if doc.text:
                        annotations.append(doc.text.strip())

        # Return consolidated annotation if any found
        if annotations:
            # Clean and normalize the annotation text
            consolidated = ' '.join(annotations)
            consolidated = consolidated.replace('\n', ' ').replace('\t', ' ')
            consolidated = re.sub(r'\s+', ' ', consolidated).strip()
            return consolidated
        return None

    def transform(self, element, context):
        """Transform a top-level simple element into a datatype property."""
        name = element.get('name')

        # Normal processing for other elements
        # Create property URI
        property_uri = context.get_safe_uri(context.base_uri, name, is_property=True)

        # Add datatype property definition
        context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
        context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(lower_case_initial(name))))

        # Determine range from the element type
        if element.get('type'):
            type_name = element.get('type')
            # Handle different types of references
            if ':' in type_name:  # Built-in XSD type
                range_uri = context.get_type_reference(type_name)
            elif type_name.startswith('Numeric'):  # Custom numeric type
                range_uri = context.XSD.decimal
            else:  # Custom type
                range_uri = context.get_safe_uri(context.base_uri, type_name)
        else:
            # Handle inline simple type
            simple_type = element.find(f'.//{XS_NS}simpleType')
            if simple_type is not None:
                restriction = simple_type.find(f'.//{XS_NS}restriction')
                if restriction is not None and restriction.get('base'):
                    base_type = restriction.get('base')
                    if ':' in base_type:  # XSD built-in type
                        range_uri = context.get_type_reference(base_type)
                    else:  # Custom type
                        range_uri = context.get_safe_uri(context.base_uri, base_type)
                else:
                    # Default to string if no base type found
                    range_uri = context.XSD.string
            else:
                # Default to string if no type info available
                range_uri = context.XSD.string

        # Add range to property
        context.graph.add((property_uri, context.RDFS.range, range_uri))

        # Add functional property if appropriate
        from xsd_to_owl.auxiliary.xsd_parsers import is_functional
        if is_functional(element):
            context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

        # Add consolidated documentation if available
        annotation = self._extract_consolidated_annotation(element)
        if annotation:
            context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(annotation)))

        # Mark the element as processed
        context.mark_processed(element, self.rule_id)

        # Prevent other rules from processing this element
        context.mark_processed(element, "top_level_element")  # Prevent standard class creation

        return property_uri


class ElementReferenceRule(XSDVisitor):
    """
    Rule: Handle xs:element with ref attribute.

    This rule consolidates annotations and creates proper properties
    for element references, avoiding duplicate classes and ensuring
    correct property types (datatype vs object).
    """

    @property
    def rule_id(self):
        return "element_reference_rule"

    @property
    def description(self):
        return "Handle xs:element with ref attribute"

    # Higher priority than other element rules
    @property
    def priority(self):
        return 110

    @check_already_processed
    def matches(self, element, context):
        # Match elements with 'ref' attribute
        if element.tag == f"{XS_NS}element" and 'ref' in element.attrib:
            ref_name = element.get('ref')
            print(f"DEBUG: ElementReferenceRule.matches: Found element with ref='{ref_name}'")
            
            # Special debug for IncotermCode
            if ref_name == "IncotermCode":
                print(f"DEBUG: FOUND INCOTERMCODE ELEMENT!")
                print(f"DEBUG: Element parent tag: {element.getparent().tag if element.getparent() is not None else 'None'}")
                print(f"DEBUG: Element attributes: {element.attrib}")
                
                # Print the parent hierarchy
                parent = element.getparent()
                hierarchy = []
                while parent is not None:
                    if parent.tag == f"{XS_NS}element" and parent.get('name'):
                        hierarchy.append(f"element:{parent.get('name')}")
                    elif parent.tag == f"{XS_NS}choice":
                        hierarchy.append("choice")
                    elif parent.tag == f"{XS_NS}complexType":
                        hierarchy.append("complexType")
                    elif parent.tag == f"{XS_NS}sequence":
                        hierarchy.append("sequence")
                    else:
                        hierarchy.append(parent.tag)
                    parent = parent.getparent()
                
                print(f"DEBUG: Parent hierarchy for IncotermCode: {' -> '.join(reversed(hierarchy))}")
            
            # Check if it's inside a choice element
            if element.getparent() is not None and element.getparent().tag == f"{XS_NS}choice":
                print(f"DEBUG: ElementReferenceRule.matches: Element {ref_name} is inside a choice element")
                
                # Print the parent hierarchy
                parent = element.getparent()
                hierarchy = []
                while parent is not None:
                    if parent.tag == f"{XS_NS}element" and parent.get('name'):
                        hierarchy.append(parent.get('name'))
                    elif parent.tag == f"{XS_NS}choice":
                        hierarchy.append("choice")
                    elif parent.tag == f"{XS_NS}complexType":
                        hierarchy.append("complexType")
                    elif parent.tag == f"{XS_NS}sequence":
                        hierarchy.append("sequence")
                    parent = parent.getparent()
                
                print(f"DEBUG: Parent hierarchy for {ref_name}: {' -> '.join(reversed(hierarchy))}")
            
            return True
        return False

    def _find_referenced_element(self, element, context):
        """Find the element referenced by a ref attribute."""
        ref_name = element.get('ref')
        if not ref_name:
            return None

        # First try to find the element in the current document
        schema_root = element.getroottree().getroot()
        ref_elements = schema_root.findall(f".//*[@name='{ref_name}']")
        
        if ref_elements:
            return ref_elements[0]
            
        # If not found, try to find it in other loaded documents
        # This is important for handling references to elements defined in other XSD files
        if hasattr(context, 'all_elements'):
            for elem_name, elem in context.all_elements.items():
                if elem_name == ref_name:
                    return elem
                    
        # If still not found, log a warning
        print(f"Warning: Referenced element '{ref_name}' not found in any loaded document")
        return None

    def _get_element_type(self, element):
        """Determine if an element is a simple type or complex type."""
        # Check for inline simple/complex type
        has_simple_type = element.find(f'.//{XS_NS}simpleType') is not None
        has_complex_type = element.find(f'.//{XS_NS}complexType') is not None

        # Check for type attribute
        type_attr = element.get('type')
        is_built_in_type = type_attr is not None and ':' in type_attr
        is_numeric_type = type_attr is not None and type_attr.startswith('Numeric')

        # Determine element type
        if has_complex_type:
            return "complex"
        elif has_simple_type or is_built_in_type or is_numeric_type:
            return "simple"
        elif type_attr:
            # Reference to custom type - need to check if it's complex or simple
            return "reference"
        else:
            # Default to complex if we can't determine
            return "complex"

    def _handle_element_in_choice(self, element, property_uri, context):
        """
        Handle domain assignment for elements inside choice elements.
        This is a general solution for all element references inside choice elements.
        
        Args:
            element: The element being processed
            property_uri: The URI of the property being created
            context: The transformation context
            
        Returns:
            bool: True if domain was set, False otherwise
        """
        choice_element = element.getparent()
        ref_name = element.get('ref')
        property_name = lower_case_initial(ref_name)
        print(f"DEBUG: Element {ref_name} (property {property_name}) is inside a choice element")
        
        # Find the parent of the choice element (which should be a complexType)
        complex_type_parent = choice_element.getparent()
        print(f"DEBUG: Parent of choice element: {complex_type_parent.tag if complex_type_parent is not None else 'None'}")
        
        if complex_type_parent is not None and complex_type_parent.tag == f"{XS_NS}complexType":
            # Find the parent of the complexType (which should be an element)
            element_parent = complex_type_parent.getparent()
            print(f"DEBUG: Parent of complexType: {element_parent.tag if element_parent is not None else 'None'}")
            
            if element_parent is not None and element_parent.tag == f"{XS_NS}element" and element_parent.get('name'):
                parent_name = element_parent.get('name')
                parent_uri = context.get_safe_uri(context.base_uri, parent_name)
                print(f"DEBUG: Found parent element {parent_name} for choice containing {ref_name}")
                
                # Store the reference in the global dictionary
                property_name = lower_case_initial(ref_name)
                
                # Store both the original element name and the lowercase property name
                CHOICE_ELEMENT_REFS[ref_name] = {
                    'parent_name': parent_name,
                    'parent_uri': str(parent_uri)
                }
                
                CHOICE_ELEMENT_REFS[property_name] = {
                    'parent_name': parent_name,
                    'parent_uri': str(parent_uri)
                }
                
                print(f"DEBUG: Stored reference for element {ref_name} and property {property_name} with parent {parent_name}")
                
                # Ensure the parent class exists
                if (parent_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                    print(f"DEBUG: Creating class for parent {parent_name}")
                    context.graph.add((parent_uri, context.RDF.type, context.OWL.Class))
                    context.graph.add((parent_uri, context.RDFS.label, rdflib.Literal(parent_name)))
                
                # Set the domain directly
                print(f"DEBUG: Setting domain for {ref_name} to {parent_name}")
                context.graph.add((property_uri, context.RDFS.domain, parent_uri))
                
                # Verify the domain was set
                if (property_uri, context.RDFS.domain, parent_uri) in context.graph:
                    print(f"DEBUG: Domain successfully set for {ref_name}")
                else:
                    print(f"DEBUG: Failed to set domain for {ref_name}")
                
                return True
        
        # If we couldn't find a direct parent, try the normal approach with the choice element
        print(f"DEBUG: Falling back to normal domain setting for {ref_name}")
        set_property_domain(context, property_uri, choice_element)
        return False

    def transform(self, element, context):
        # Get the referenced element name
        ref_name = element.get('ref')
        print(f"DEBUG: ElementReferenceRule.transform: Processing element with ref='{ref_name}'")
        
        # Special debug for IncotermCode
        if ref_name == "IncotermCode":
            print(f"DEBUG: TRANSFORMING INCOTERMCODE ELEMENT!")
            print(f"DEBUG: Element parent tag: {element.getparent().tag if element.getparent() is not None else 'None'}")
        
        # Find the referenced element definition
        ref_element = self._find_referenced_element(element, context)
        if not ref_element:
            print(f"Warning: Referenced element '{ref_name}' not found")
            return None

        # Determine if referenced element is simple or complex type
        element_type = self._get_element_type(ref_element)
        print(f"DEBUG: ElementReferenceRule.transform: Element {ref_name} has type {element_type}")

        # Create appropriate property based on element type
        if element_type == "simple":
            # Create data property
            property_uri = context.get_safe_uri(context.base_uri, ref_name, is_property=True)
            context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
            
            # Special handling for elements inside choice
            if element.getparent() is not None and element.getparent().tag == f"{XS_NS}choice":
                print(f"DEBUG: ElementReferenceRule.transform: Element {ref_name} is inside a choice element, calling _handle_element_in_choice")
                domain_set = self._handle_element_in_choice(element, property_uri, context)
                print(f"DEBUG: ElementReferenceRule.transform: _handle_element_in_choice returned {domain_set}")
                if domain_set:
                    # If domain was set by _handle_element_in_choice, we can skip the rest of the property creation
                    # and just add the range
                    print(f"DEBUG: ElementReferenceRule.transform: Adding range {range_uri} to property {ref_name}")
                    context.graph.add((property_uri, context.RDFS.range, range_uri))
                    
                    # Add label
                    context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(lower_case_initial(ref_name))))
                    
                    # Add functional property if appropriate
                    from xsd_to_owl.auxiliary.xsd_parsers import is_functional
                    if is_functional(element):
                        context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))
                    
                    # Mark as processed
                    context.mark_processed(element, self.rule_id)
                    
                    return property_uri
            else:
                # Normal domain setting
                set_property_domain(context, property_uri, element)

            # Determine range
            type_attr = ref_element.get('type')
            if type_attr:
                if ':' in type_attr:  # Built-in XSD type
                    range_uri = context.get_type_reference(type_attr)
                elif type_attr.startswith('Numeric'):  # Custom numeric type
                    range_uri = context.XSD.decimal
                else:  # Custom type
                    range_uri = context.get_safe_uri(context.base_uri, type_attr)
            else:
                # Handle inline simple type
                simple_type = ref_element.find(f'.//{XS_NS}simpleType')
                if simple_type is not None:
                    restriction = simple_type.find(f'.//{XS_NS}restriction')
                    if restriction is not None and restriction.get('base'):
                        base_type = restriction.get('base')
                        if ':' in base_type:  # XSD built-in type
                            range_uri = context.get_type_reference(base_type)
                        else:  # Custom type
                            range_uri = context.get_safe_uri(context.base_uri, base_type)
                    else:
                        range_uri = context.XSD.string
                else:
                    range_uri = context.XSD.string

            context.graph.add((property_uri, context.RDFS.range, range_uri))
        else:
            # Create object property
            property_uri = context.get_safe_uri(context.base_uri, ref_name, is_property=True)
            class_uri = context.get_safe_uri(context.base_uri, ref_name)

            context.graph.add((property_uri, context.RDF.type, context.OWL.ObjectProperty))
            
            # Special handling for elements inside choice
            if element.getparent() is not None and element.getparent().tag == f"{XS_NS}choice":
                domain_set = self._handle_element_in_choice(element, property_uri, context)
                if domain_set:
                    # If domain was set by _handle_element_in_choice, we can skip the rest of the property creation
                    # and just add the range
                    context.graph.add((property_uri, context.RDFS.range, class_uri))
                    
                    # Add label
                    context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(lower_case_initial(ref_name))))
                    
                    # Add functional property if appropriate
                    from xsd_to_owl.auxiliary.xsd_parsers import is_functional
                    if is_functional(element):
                        context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))
                    
                    # Mark as processed
                    context.mark_processed(element, self.rule_id)
                    
                    return property_uri
            else:
                # Normal domain setting
                set_property_domain(context, property_uri, element)
                
            context.graph.add((property_uri, context.RDFS.range, class_uri))

        # Add label
        context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(lower_case_initial(ref_name))))

        # Add functional property if appropriate
        from xsd_to_owl.auxiliary.xsd_parsers import is_functional
        if is_functional(element):
            context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

        # Add consolidated documentation from both elements
        annotation = TopLevelSimpleElementRule._extract_consolidated_annotation(ref_element, element)
        if annotation:
            context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(annotation)))

        # Also ensure the referenced element is properly documented if it's a class
        if element_type != "simple" and not context.is_processed(ref_element, "class_definition"):
            class_uri = context.get_safe_uri(context.base_uri, ref_name)
            context.graph.add((class_uri, context.RDF.type, context.OWL.Class))
            context.graph.add((class_uri, context.RDFS.label, rdflib.Literal(ref_name)))

            # Add documentation to the class as well
            ref_annotation = TopLevelSimpleElementRule._extract_consolidated_annotation(ref_element)
            if ref_annotation:
                context.graph.add((class_uri, context.SKOS.definition, rdflib.Literal(ref_annotation)))

        # Mark as processed
        context.mark_processed(element, self.rule_id)

        return property_uri




class ChildElementPropertyRule(XSDVisitor):
    """
    Rule: Process child elements of complex types as properties.
    Uses element metadata to determine parent class.
    """

    @property
    def rule_id(self):
        return "child_element_property"

    @property
    def description(self):
        return "Transform child elements of complex types to properties"

    @property
    def priority(self):
        return 75  # Run after complex types but before other property rules

    @check_already_processed
    def matches(self, element, context):
        # Match element that has parent metadata (from AnonymousComplexTypeRule)
        if element.tag != f"{XS_NS}element":
            return False

        # Debug all element matches
        name = element.get('name')
        ref = element.get('ref')

        # Check if this element has been marked with parent metadata
        metadata = context.get_element_metadata(element)

        # Don't check if the element has been processed by other rules!
        # Just check if it has parent metadata and needs a property created

        if metadata and 'parent_uri' in metadata:
            # Check if property already exists for this element
            property_name = lower_case_initial(name or ref)
            property_uri = context.get_property_uri(property_name)
            if not property_uri:  # Property doesn't exist yet
                # Also check if this specific rule has already processed it
                if not context.is_processed(element, self.rule_id):
                    # This element needs a property!
                    return True

        return False

    def transform(self, element, context):
        from xsd_to_owl.auxiliary.property_utils import register_property
        from xsd_to_owl.auxiliary.property_utils import is_datatype_property
        from xsd_to_owl.auxiliary.property_utils import determine_datatype_range
        from xsd_to_owl.config.special_cases import should_never_be_object_property
        
        # Get child element attributes
        child_name = element.get('name')
        child_ref = element.get('ref')

        print(f"\n====== TRANSFORMING PROPERTY: {child_name or child_ref} ======")

        # Check for complex type child
        complex_type = element.find(f"./{XS_NS}complexType")
        print(f"  Has direct complexType child: {complex_type is not None}")

        if not (child_name or child_ref):
            print("  SKIP: No name or ref")
            return None  # Skip if no name or ref
            
        # Check if this element should never be an object property
        child_type = element.get('type')
        if child_name and should_never_be_object_property(child_name, child_type):
            print(f"DEBUG: Skipping {child_name} as it should never be an object property")
            return None

        # Use the child's local name for the property name
        property_name = child_name if child_name else child_ref
        property_name = lower_case_initial(property_name)  # Ensure first letter is lowercase

        # Get or create property URI
        property_uri = context.get_safe_uri(context.base_uri, property_name, is_property=True)
        print(f"  Property URI: {property_uri}")
        
        # Check if property already exists in the graph
        existing_datatype = (property_uri, context.RDF.type, context.OWL.DatatypeProperty) in context.graph
        if existing_datatype:
            print(f"  Property {property_name} already exists as a datatype property - skipping")
            return None

        # Determine if this should be a datatype or object property
        datatype_prop = is_datatype_property(element, property_name)
        print(f"  Is datatype property: {datatype_prop}")

        # For references, try to find the referenced element
        referenced_element = None
        if child_ref:
            schema_root = element.getroottree().getroot()
            from xsd_to_owl.auxiliary.property_utils import find_referenced_element
            referenced_element = find_referenced_element(element, child_ref, schema_root)
            print(f"  Referenced element found: {referenced_element is not None}")

            # If we have a reference and couldn't determine from the element, check the referenced element
            if referenced_element is not None and not datatype_prop:
                datatype_prop = is_datatype_property(referenced_element, property_name)
                print(f"  Is datatype property (from reference): {datatype_prop}")

        # Create the appropriate property type
        if datatype_prop:
            # Determine range for datatype property
            range_uri = determine_datatype_range(element, property_name, context)
            print(f"  Creating datatype property with range: {range_uri}")

            # Create datatype property
            context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
            context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(property_name)))
            set_property_domain(context, property_uri, element)
            context.graph.add((property_uri, context.RDFS.range, range_uri))

            # Register it
            register_property(property_name, property_uri, is_datatype=True)
        else:
            # For references or complex types, create an object property
            target_name = child_ref if child_ref else child_name
            target_uri = context.get_safe_uri(context.base_uri, target_name)
            print(f"  Creating object property with range: {target_uri}")

            # Create object property
            context.graph.add((property_uri, context.RDF.type, context.OWL.ObjectProperty))
            context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(property_name)))
            set_property_domain(context, property_uri, element)
            context.graph.add((property_uri, context.RDFS.range, target_uri))

            # Register it
            register_property(property_name, property_uri, is_datatype=False)

        # Extract domain class name from the graph
        parent_name = "Unknown"
        for s, p, o in context.graph:
            if s == property_uri and p == context.RDFS.domain:
                # Extract the class name from the URI
                parent_name = str(o).split('/')[-1]
                break

        print(f"DEBUG: Created property for {child_name or child_ref} in {parent_name}")

        # Add functional property if appropriate
        from xsd_to_owl.auxiliary.xsd_parsers import is_functional
        if is_functional(element):
            context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

        # Add documentation if available
        from xsd_to_owl.auxiliary.xsd_parsers import get_documentation
        doc = get_documentation(element)
        if doc:
            context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc)))

        # Mark element as processed
        context.mark_processed(element, self.rule_id)
        print(f"  Property created successfully: {property_name}")

        return property_uri


class ComplexElementPropertyRule(XSDVisitor):
    """
    Rule to create object properties for elements that have already been
    processed as classes but should also be properties of parent elements.
    """

    @property
    def rule_id(self):
        return "complex_element_property"

    @property
    def description(self):
        return "Create properties for elements that are both classes and properties"

    @property
    def priority(self):
        return 90  # Run after anonymous_complex_type (100) but before other property rules

    @check_already_processed
    def matches(self, element, context):
        # Only match elements
        if element.tag != f"{XS_NS}element":
            return False

        # Must have a name
        name = element.get('name')
        if not name:
            return False

        # Check if this element should never be an object property
        from xsd_to_owl.config.special_cases import should_never_be_object_property
        type_name = element.get('type')
        if should_never_be_object_property(name, type_name):
            print(f"DEBUG: Skipping {name} as it should never be an object property")
            return False

        # Must have a complexType child
        has_complex_child = element.find(f"./{XS_NS}complexType") is not None
        if not has_complex_child:
            return False

        # Must have parent metadata
        metadata = context.get_element_metadata(element)
        if not metadata or 'parent_uri' not in metadata:
            return False

        # Check if property already exists
        from xsd_to_owl.auxiliary.uri_utils import lower_case_initial
        property_name = lower_case_initial(name)
        property_uri = context.get_property_uri(property_name)
        property_exists = property_uri is not None

        # Check if property is already registered as a datatype property
        from xsd_to_owl.auxiliary.property_utils import get_registered_property
        registered = get_registered_property(property_name)
        if registered and registered.get('is_datatype') is True:
            print(f"DEBUG: Skipping {name} as it is already registered as a datatype property")
            return False

        # Match if no property exists yet
        return not property_exists

    def transform(self, element, context):
        name = element.get('name')
        from xsd_to_owl.auxiliary.uri_utils import lower_case_initial
        property_name = lower_case_initial(name)

        # Get parent information
        metadata = context.get_element_metadata(element)
        parent_uri = metadata['parent_uri']
        parent_name = metadata.get('parent_name', 'Unknown')

        print(f"\n====== CREATING COMPLEX ELEMENT PROPERTY: {name} ======")
        # print(f"  Parent: {parent_name}")

        # Create property URI
        property_uri = context.get_safe_uri(context.base_uri, property_name, is_property=True)

        # Get class URI for the range
        class_uri = context.get_safe_uri(context.base_uri, name)

        # Create object property
        context.graph.add((property_uri, context.RDF.type, context.OWL.ObjectProperty))
        context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(property_name)))
        set_property_domain(context, property_uri, element)
        # context.graph.add((property_uri, context.RDFS.domain, parent_uri))
        context.graph.add((property_uri, context.RDFS.range, class_uri))

        # Add functional property if appropriate
        from xsd_to_owl.auxiliary.xsd_parsers import is_functional
        if is_functional(element):
            context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

        # Add documentation if available
        from xsd_to_owl.auxiliary.xsd_parsers import get_documentation
        doc = get_documentation(element)
        if doc:
            context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc)))

        # Register the property
        from xsd_to_owl.auxiliary.property_utils import register_property
        register_property(property_name, property_uri, is_datatype=False)

        # Register in context too for consistency
        context.register_property_uri(property_name, property_uri)

        print(f"  Created object property for complex element: {property_name}")
        print(f"  Domain: {parent_uri}")
        print(f"  Range: {class_uri}")

        # Mark as processed by this rule
        context.mark_processed(element, self.rule_id)

        return property_uri


class SandwichElementPropertyRule(XSDVisitor):
    """Rule to create properties for elements that are both classes and property targets."""

    @property
    def rule_id(self):
        return "sandwich_element_property"

    @property
    def description(self):
        return "Create properties for elements that are both classes and property targets"

    @property
    def priority(self):
        return 200  # Run after class creation but before other property rules

    def matches(self, element, context):
        if element.tag != f"{XS_NS}element":
            return False

        # Check for sandwich metadata flag
        metadata = context.get_element_metadata(element)
        if metadata and metadata.get('is_sandwich') == True:
            # Should already be a class but needs property creation too
            return True

        return False

    def transform(self, element, context):
        name = element.get('name') or element.get('ref')
        property_name = lower_case_initial(name)

        # Get metadata
        # metadata = context.get_element_metadata(element)
        # parent_uri = metadata['parent_uri']

        # Get class URI
        target_uri = context.get_safe_uri(context.base_uri, name)

        # Create property URI
        property_uri = context.get_safe_uri(context.base_uri, property_name, is_property=True)

        # Create object property
        context.graph.add((property_uri, context.RDF.type, context.OWL.ObjectProperty))
        context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(property_name)))
        set_property_domain(context, property_uri, element)
        context.graph.add((property_uri, context.RDFS.range, target_uri))

        # Register the property
        from xsd_to_owl.auxiliary.property_utils import register_property
        register_property(property_name, property_uri, is_datatype=False)

        # Mark as processed
        context.mark_processed(element, self.rule_id)

        return property_uri


class ReferenceTrackingRule(XSDVisitor):
    """Rule to track element references and associate them with parent contexts."""

    @property
    def rule_id(self):
        return "reference_tracking"

    @property
    def description(self):
        return "Track element references and their parent contexts"

    @property
    def priority(self):
        return 500  # Run very early in the process, before class creation

    def matches(self, element, context):
        # Match elements with 'ref' attribute
        if element.tag != f"{XS_NS}element":
            return False

        ref = element.get('ref')
        return ref is not None

    def transform(self, element, context):
        """Since there are side-effects, this should not be considered a Debug Rule. """
        ref = element.get('ref')

        # Check if this element has parent metadata from previous processing
        metadata = context.get_element_metadata(element)
        parent_uri = metadata.get('parent_uri') if metadata else None

        if parent_uri:
            # Store the reference context for later use
            # Maintain a list of all parent contexts for each referenced element
            if not hasattr(context, '_reference_contexts'):
                context._reference_contexts = {}

            if ref not in context._reference_contexts:
                context._reference_contexts[ref] = []

            # Add this parent context
            context._reference_contexts[ref].append({
                'parent_uri': parent_uri,
                'parent_name': metadata.get('parent_name'),
                'from_element': element
            })

            print(f"Tracked reference: {ref} used in {metadata.get('parent_name')}")

        # Don't transform anything here, just track
        return None


class ReferencedElementDomainRule(XSDVisitor):
    """Rule to ensure referenced elements have proper domains set."""

    @property
    def rule_id(self):
        return "referenced_element_domain"

    @property
    def description(self):
        return "Set domains for properties created from referenced elements"

    @property
    def priority(self):
        return 20  # Run near the end, after all properties are created

    def matches(self, element, context):
        # Run once at the end on the schema element
        if not element.tag.endswith("schema"):
            return False

        # Only run if we have reference contexts to process
        return hasattr(context, '_reference_contexts') and bool(context._reference_contexts)

    def transform(self, element, context):
        from xsd_to_owl.auxiliary.property_utils import get_registered_property
        from xsd_to_owl.auxiliary.uri_utils import lower_case_initial

        print("\n==== SETTING DOMAINS FOR REFERENCED ELEMENTS ====")
        fixed_count = 0

        # Process each referenced element
        for ref_name, contexts in context._reference_contexts.items():
            # Generate the property name (lowercase initial)
            property_name = lower_case_initial(ref_name)

            # Get the property URI
            property_uri = get_registered_property(property_name)

            if not property_uri:
                print(f"Warning: Property {property_name} not found for reference {ref_name}")
                continue

            print(f"Processing referenced element: {ref_name}")
            print(f"  Property: {property_name} -> {property_uri}")
            print(f"  Referenced in {len(contexts)} contexts")

            # Add each parent as a domain
            for ref_context in contexts:
                parent_uri = ref_context['parent_uri']
                parent_name = ref_context['parent_name']

                # Check if this domain relationship already exists
                if (property_uri, context.RDFS.domain, parent_uri) in context.graph:
                    print(f"  Domain already set: {parent_name}")
                    continue

                # Add domain triple
                # context.graph.add((property_uri, context.RDFS.domain, parent_uri))
                # print(f"  Added domain: {parent_name}")
                set_property_domain(context, property_uri, ref_context['from_element'])
                fixed_count += 1

        print(f"Fixed {fixed_count} domain references")
        return None


def set_property_domain(context, property_uri, element):
    """
    Sets the appropriate domain for a property based on metadata or parent element.

    This utility function centralizes domain setting logic to ensure consistency
    across all property-creating rules.

    Args:
        context: The transformation context
        property_uri: URI of the property
        element: The XML element being processed

    Returns:
        bool: True if a domain was set, False otherwise
    """
    # Initialize property domains tracking if not already present
    if not hasattr(context, '_property_domains'):
        context._property_domains = {}
    
    # First check if we have metadata with parent_uri
    metadata = context.get_element_metadata(element)
    if metadata and 'parent_uri' in metadata:
        parent_uri = metadata['parent_uri']
        if parent_uri:
            # Track this domain for the property
            if property_uri not in context._property_domains:
                context._property_domains[property_uri] = set()
            context._property_domains[property_uri].add(parent_uri)
            
            # For backward compatibility, still add the domain directly
            # This will be replaced with a union domain in the DomainFixerRule
            if (property_uri, context.RDFS.domain, parent_uri) not in context.graph:
                context.graph.add((property_uri, context.RDFS.domain, parent_uri))
            return True

    # If no metadata, try to find parent element
    parent_uri = find_parent_element(element, context)
    if parent_uri:
        # Track this domain for the property
        if property_uri not in context._property_domains:
            context._property_domains[property_uri] = set()
        context._property_domains[property_uri].add(parent_uri)
        
        # For backward compatibility, still add the domain directly
        # This will be replaced with a union domain in the DomainFixerRule
        if (property_uri, context.RDFS.domain, parent_uri) not in context.graph:
            context.graph.add((property_uri, context.RDFS.domain, parent_uri))
        return True

    # No domain found or set
    return False


class ChoiceElementPropertyRule(XSDVisitor):
    """
    Rule: xs:choice element ->
          Set of OWL properties with constraints to ensure exactly one is used.
          
    This rule handles xs:choice elements by:
    1. Creating a property for each option in the choice
    2. Adding OWL constraints to specify that exactly one of these properties must have a value
    3. Using owl:cardinality=1 on a union of properties
    """

    @property
    def rule_id(self):
        return "choice_element_property"

    @property
    def description(self):
        return "Transform xs:choice elements to properties with disjointness and cardinality constraints"

    @property
    def priority(self):
        return 120  # Higher than standard property rules but lower than specialized rules

    @check_already_processed
    def matches(self, element, context):
        # Match only xs:choice elements
        if element.tag != f"{XS_NS}choice":
            return False
            
        # Must have at least one child element
        child_elements = element.findall(f".//{XS_NS}element")
        return len(child_elements) > 0

    def transform(self, element, context):
        # Get parent element to determine domain
        parent_element = element.getparent()
        if parent_element is None:
            logging.warning("Choice element has no parent, cannot create properties")
            return None
            
        # Find all child elements in the choice
        child_elements = element.findall(f".//{XS_NS}element")
        if not child_elements:
            logging.warning("Choice element has no child elements, skipping")
            return None
            
        # Create properties for each option in the choice
        property_uris = []
        for child in child_elements:
            name = child.get('name')
            ref_name = child.get('ref')
            
            if not name and not ref_name:
                logging.warning(f"Child element in choice has no name or ref, skipping")
                continue
            
            # Use name or ref_name
            element_name = name if name else ref_name
            print(f"DEBUG: Processing choice element child: {element_name} (name={name}, ref={ref_name})")
            
            # Create property URI
            property_uri = context.get_safe_uri(context.base_uri, element_name, is_property=True)
            property_uris.append(property_uri)
            
            # Determine property type and range based on child element
            element_name = name if name else ref_name
            
            if ref_name:
                # For referenced elements, find the referenced element definition
                ref_element = None
                schema_root = child.getroottree().getroot()
                ref_elements = schema_root.findall(f".//*[@name='{ref_name}']")
                
                if ref_elements:
                    ref_element = ref_elements[0]
                    print(f"DEBUG: Found referenced element {ref_name}")
                else:
                    print(f"DEBUG: Referenced element {ref_name} not found")
                
                if ref_element is not None:
                    # Get type from referenced element
                    type_name = ref_element.get('type')
                    is_datatype = False
                    
                    if type_name:
                        # Check if it's a simple type
                        if ':' in type_name or type_name.startswith("Numeric") or "Decimal" in type_name:
                            is_datatype = True
                            range_uri = context.get_type_reference(type_name)
                        else:
                            # Complex type reference
                            range_uri = context.get_safe_uri(context.base_uri, type_name)
                    else:
                        # Check for inline simple or complex type
                        simple_type = ref_element.find(f".//{XS_NS}simpleType")
                        complex_type = ref_element.find(f".//{XS_NS}complexType")
                        
                        if simple_type is not None and complex_type is None:
                            is_datatype = True
                            # Get base type from restriction
                            restriction = simple_type.find(f".//{XS_NS}restriction")
                            if restriction is not None and restriction.get('base'):
                                base_type = restriction.get('base')
                                range_uri = context.get_type_reference(base_type)
                            else:
                                range_uri = context.XSD.string
                        elif complex_type is not None:
                            # Create a class for this complex type if it doesn't exist
                            class_uri = context.get_safe_uri(context.base_uri, ref_name)
                            if (class_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                                context.graph.add((class_uri, context.RDF.type, context.OWL.Class))
                                context.graph.add((class_uri, context.RDFS.label, rdflib.Literal(ref_name)))
                            range_uri = class_uri
                        else:
                            # Default to string if no type information
                            is_datatype = True
                            range_uri = context.XSD.string
                else:
                    # Default to string if referenced element not found
                    is_datatype = True
                    range_uri = context.XSD.string
            else:
                # For named elements, use the type attribute
                type_name = child.get('type')
                is_datatype = False
                
                if type_name:
                    # Check if it's a simple type
                    if ':' in type_name or type_name.startswith("Numeric") or "Decimal" in type_name:
                        is_datatype = True
                        range_uri = context.get_type_reference(type_name)
                    else:
                        # Complex type reference
                        range_uri = context.get_safe_uri(context.base_uri, type_name)
                else:
                    # Check for inline simple or complex type
                    simple_type = child.find(f".//{XS_NS}simpleType")
                    complex_type = child.find(f".//{XS_NS}complexType")
                    
                    if simple_type is not None and complex_type is None:
                        is_datatype = True
                        # Get base type from restriction
                        restriction = simple_type.find(f".//{XS_NS}restriction")
                        if restriction is not None and restriction.get('base'):
                            base_type = restriction.get('base')
                            range_uri = context.get_type_reference(base_type)
                        else:
                            range_uri = context.XSD.string
                    elif complex_type is not None:
                        # Create a class for this complex type if it doesn't exist
                        class_uri = context.get_safe_uri(context.base_uri, name)
                        if (class_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                            context.graph.add((class_uri, context.RDF.type, context.OWL.Class))
                            context.graph.add((class_uri, context.RDFS.label, rdflib.Literal(name)))
                        range_uri = class_uri
                    else:
                        # Default to string if no type information
                        is_datatype = True
                        range_uri = context.XSD.string
            
            # Create property
            if is_datatype:
                context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
            else:
                context.graph.add((property_uri, context.RDF.type, context.OWL.ObjectProperty))
                
            element_name = name if name else ref_name
            context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(lower_case_initial(element_name))))
            set_property_domain(context, property_uri, parent_element)
            context.graph.add((property_uri, context.RDFS.range, range_uri))
            
            # Add functional property constraint
            from xsd_to_owl.auxiliary.xsd_parsers import is_functional, get_documentation
            if is_functional(child):
                context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))
            
            # Add documentation if available
            doc = get_documentation(child)
            if doc:
                context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc)))
            
            # Store reference in CHOICE_ELEMENT_REFS for domain fixing
            if ref_name:
                # Get parent element name
                parent_name = None
                if parent_element.tag == f"{XS_NS}element" and parent_element.get('name'):
                    parent_name = parent_element.get('name')
                elif parent_element.getparent() is not None and parent_element.getparent().tag == f"{XS_NS}element" and parent_element.getparent().get('name'):
                    parent_name = parent_element.getparent().get('name')
                
                if parent_name:
                    parent_uri = context.get_safe_uri(context.base_uri, parent_name)
                    
                    # Store both the original element name and the lowercase property name
                    CHOICE_ELEMENT_REFS[ref_name] = {
                        'parent_name': parent_name,
                        'parent_uri': str(parent_uri)
                    }
                    
                    property_name = lower_case_initial(ref_name)
                    CHOICE_ELEMENT_REFS[property_name] = {
                        'parent_name': parent_name,
                        'parent_uri': str(parent_uri)
                    }
                    
                    print(f"DEBUG: Stored reference for element {ref_name} and property {property_name} with parent {parent_name}")
                
            # Mark the child element as processed
            context.mark_processed(child, "simple_type_property")
            context.mark_processed(child, "complex_type_reference")
            context.mark_processed(child, "inline_simple_type_property")
            context.mark_processed(child, "element_reference")
        
        # Create OWL constraints to ensure exactly one property is used
        if len(property_uris) > 1:
            # Create a blank node for the union of properties
            union_node = BNode()
            
            # Create a list of properties for owl:unionOf
            # The collection method in rdflib.Graph only takes the subject as parameter
            # and returns a Collection object that we can initialize with our list
            collection = context.graph.collection(union_node)
            for prop_uri in property_uris:
                collection.append(prop_uri)
            
            # Add a comment to explain the choice constraint
            choice_comment = f"This represents an xs:choice element with {len(property_uris)} options. Exactly one of these properties must be used."
            for prop_uri in property_uris:
                context.graph.add((prop_uri, context.RDFS.comment, rdflib.Literal(choice_comment)))
            
            # Mark the choice element as processed
            context.mark_processed(element, self.rule_id)
            
            logging.info(f"Created {len(property_uris)} properties for choice element with constraint")
            return property_uris
        elif len(property_uris) == 1:
            # Only one option, no need for constraints
            context.mark_processed(element, self.rule_id)
            return property_uris[0]
        else:
            return None


class DomainFixerRule(XSDVisitor):
    """Rule that adds domains to referenced properties based on tracked references.
    The addresses a specific scenario that can't be handled by regular property creation rules: `DomainFixerRule`
1. **Referenced Elements**: When an element is defined once and referenced multiple times in different contexts, each reference should have its own domain relationship.
2. **Two-Phase Processing**: Property creation typically happens when the element is first defined. However, at that time, you don't know all the places where it will be referenced.
3. **Comprehensive Domain Collection**: The runs at the end of processing and adds all the domains gathered by the . `DomainFixerRule``ReferenceTrackingRule`
4. **Union Domains**: When a property can be used in multiple classes, the domain is represented as a UNION of those classes.
"""
    # Import URIRef
    from rdflib import URIRef

    @property
    def rule_id(self):
        return "domain_fixer"

    @property
    def description(self):
        return "Add proper domains to properties created from referenced elements using owl:unionOf for multiple domains"

    @property
    def priority(self):
        return 10  # Run near the end of processing

    def matches(self, element, context):
        # Run once on the schema element
        if not element.tag.endswith("schema"):
            return False

        # Run if we have tracked references or property domains
        has_references = hasattr(context, '_reference_contexts') and bool(context._reference_contexts)
        has_property_domains = hasattr(context, '_property_domains') and bool(context._property_domains)
        
        return has_references or has_property_domains

    def transform(self, element, context):
        domains_added = 0
        union_domains_created = 0
        
        # Process tracked property domains
        if hasattr(context, '_property_domains'):
            for property_uri, domains in context._property_domains.items():
                if len(domains) > 1:
                    # Create a union class for multiple domains
                    self._create_union_domain(context, property_uri, domains)
                    union_domains_created += 1
        
        # Process reference contexts (for backward compatibility)
        if hasattr(context, '_reference_contexts'):
            reference_contexts = context._reference_contexts
            
            # Process each reference
            for ref_name, contexts in reference_contexts.items():
                # Get property name (lowercase initial)
                from xsd_to_owl.auxiliary.uri_utils import lower_case_initial
                property_name = lower_case_initial(ref_name)

                # Look up property URI from registry
                from xsd_to_owl.auxiliary.property_utils import get_registered_property
                property_info = get_registered_property(property_name)

                if not property_info or 'uri' not in property_info:
                    print(f"Warning: Property '{property_name}' not found in registry")
                    continue

                property_uri = property_info['uri']

                # Collect all domains for this property
                property_domains = set()
                for ctx in contexts:
                    parent_uri = ctx['parent_uri']
                    if parent_uri:
                        property_domains.add(parent_uri)
                
                # Create a union domain if we have multiple domains
                if len(property_domains) > 1:
                    self._create_union_domain(context, property_uri, property_domains)
                    union_domains_created += 1
                elif len(property_domains) == 1:
                    # Just add the single domain directly
                    parent_uri = next(iter(property_domains))
                    if (property_uri, context.RDFS.domain, parent_uri) not in context.graph:
                        context.graph.add((property_uri, context.RDFS.domain, parent_uri))
                        domains_added += 1
        
        # Process properties from CHOICE_ELEMENT_REFS
        if CHOICE_ELEMENT_REFS:
            print(f"Processing {len(CHOICE_ELEMENT_REFS)} properties from choice elements")
            
            # Find all properties without domains
            for s, p, o in context.graph.triples((None, context.RDF.type, context.OWL.DatatypeProperty)):
                # Check if property has a domain
                if (s, context.RDFS.domain, None) not in context.graph:
                    # Get property name
                    property_name = str(s).split('#')[-1]
                    print(f"DEBUG: Checking property {property_name} for domain assignment")
                    
                    # Check if we have information about this property in CHOICE_ELEMENT_REFS
                    if property_name in CHOICE_ELEMENT_REFS:
                        parent_info = CHOICE_ELEMENT_REFS[property_name]
                        parent_uri = URIRef(parent_info['parent_uri'])
                        
                        # Ensure the parent class exists
                        if (parent_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                            context.graph.add((parent_uri, context.RDF.type, context.OWL.Class))
                            context.graph.add((parent_uri, context.RDFS.label, rdflib.Literal(parent_info['parent_name'])))
                        
                        # Set the domain
                        context.graph.add((s, context.RDFS.domain, parent_uri))
                        domains_added += 1
                        print(f"Added domain {parent_info['parent_name']} to property {property_name}")
                    else:
                        # Try with the capitalized version of the property name
                        element_name = property_name[0].upper() + property_name[1:]
                        print(f"DEBUG: Trying with capitalized element name {element_name}")
                        if element_name in CHOICE_ELEMENT_REFS:
                            parent_info = CHOICE_ELEMENT_REFS[element_name]
                            parent_uri = URIRef(parent_info['parent_uri'])
                            
                            # Ensure the parent class exists
                            if (parent_uri, context.RDF.type, context.OWL.Class) not in context.graph:
                                context.graph.add((parent_uri, context.RDF.type, context.OWL.Class))
                                context.graph.add((parent_uri, context.RDFS.label, rdflib.Literal(parent_info['parent_name'])))
                            
                            # Set the domain
                            context.graph.add((s, context.RDFS.domain, parent_uri))
                            domains_added += 1
                            print(f"Added domain {parent_info['parent_name']} to property {property_name} (using element name {element_name})")

        # Debug output for CHOICE_ELEMENT_REFS
        if CHOICE_ELEMENT_REFS:
            print(f"DEBUG: CHOICE_ELEMENT_REFS contains {len(CHOICE_ELEMENT_REFS)} entries:")
            for prop_name, info in CHOICE_ELEMENT_REFS.items():
                print(f"  - {prop_name}: parent={info['parent_name']}")
        else:
            print("DEBUG: CHOICE_ELEMENT_REFS is empty")
            
        print(f"Domain fixer added {domains_added} direct domains and {union_domains_created} union domains")
        return None
        
    def _create_union_domain(self, context, property_uri, domains):
        """
        Create a union class as the domain for a property with multiple domains.
        
        Args:
            context: The transformation context
            property_uri: The property URI
            domains: Set of domain URIs
        """
        # First remove any existing domain statements
        for _, _, domain in context.graph.triples((property_uri, context.RDFS.domain, None)):
            context.graph.remove((property_uri, context.RDFS.domain, domain))
        
        # Create a blank node for the union class
        union_class = rdflib.BNode()
        
        # Add the union class type
        context.graph.add((union_class, context.RDF.type, context.OWL.Class))
        
        # Create a blank node for the union list
        union_list = self._create_rdf_list(context, list(domains))
        
        # Add the unionOf statement
        context.graph.add((union_class, context.OWL.unionOf, union_list))
        
        # Set the union class as the domain of the property
        context.graph.add((property_uri, context.RDFS.domain, union_class))
        
        # Debug output
        property_name = str(property_uri).split('#')[-1]
        domain_names = [str(d).split('#')[-1] for d in domains]
        print(f"Created union domain for property {property_name} with domains: {', '.join(domain_names)}")
    
    def _create_rdf_list(self, context, items):
        """
        Create an RDF list (for unionOf, intersectionOf, etc.)
        
        Args:
            context: The transformation context
            items: List of items to include in the RDF list
            
        Returns:
            The head of the RDF list (blank node)
        """
        if not items:
            return context.RDF.nil
            
        head = rdflib.BNode()
        context.graph.add((head, context.RDF.first, items[0]))
        
        if len(items) == 1:
            context.graph.add((head, context.RDF.rest, context.RDF.nil))
        else:
            rest = self._create_rdf_list(context, items[1:])
            context.graph.add((head, context.RDF.rest, rest))
            
        return head


class PropertyTypeFixerRule(XSDVisitor):
    """Rule to fix properties that are both datatype and object properties."""

    @property
    def rule_id(self):
        return "property_type_fixer"

    @property
    def description(self):
        return "Fix properties that are both datatype and object properties"

    @property
    def priority(self):
        return 5  # Run after domain_fixer

    def matches(self, element, context):
        # This rule doesn't match elements, it's a post-processing rule
        return element.tag.endswith("schema")

    def transform(self, element, context):
        """Fix properties that are both datatype and object properties."""
        print("\n====== FIXING PROPERTY TYPES ======")
        
        # Find properties that are both datatype and object properties
        problematic_properties = []
        for s in context.graph.subjects(context.RDF.type, context.OWL.DatatypeProperty):
            if (s, context.RDF.type, context.OWL.ObjectProperty) in context.graph:
                problematic_properties.append(s)
                
        if not problematic_properties:
            print("No properties with inconsistent types found")
            return None
            
        print(f"Found {len(problematic_properties)} properties with inconsistent types")
        
        for s in problematic_properties:
            # Get property name
            property_name = None
            for _, _, label_o in context.graph.triples((s, context.RDFS.label, None)):
                property_name = str(label_o)
                break
            
            if not property_name:
                continue
                
            print(f"  Property {property_name} is both a datatype and object property")
            
            # Check if it's in the special cases
            from xsd_to_owl.config.special_cases import should_never_be_object_property
            
            # Check if it has a comment indicating it's a Numeric type
            has_numeric_type = False
            for _, _, comment_o in context.graph.triples((s, context.RDFS.comment, None)):
                comment = str(comment_o)
                if "Original XSD type was Numeric" in comment:
                    has_numeric_type = True
                    break
            
            if should_never_be_object_property(property_name) or has_numeric_type:
                if has_numeric_type:
                    print(f"  {property_name} has a Numeric type, removing object property type")
                else:
                    print(f"  {property_name} should never be an object property, removing object property type")
                
                # Remove object property type
                context.graph.remove((s, context.RDF.type, context.OWL.ObjectProperty))
                
                # Remove any object property ranges
                object_ranges = []
                for _, _, range_o in context.graph.triples((s, context.RDFS.range, None)):
                    if range_o != context.XSD.decimal and range_o != context.XSD.string and not str(range_o).startswith(str(context.XSD)):
                        object_ranges.append(range_o)
                
                for range_o in object_ranges:
                    context.graph.remove((s, context.RDFS.range, range_o))
                    print(f"  Removed object range {range_o} from {property_name}")
            else:
                print(f"  No special case handling for {property_name}, keeping both types")
                
        return None
