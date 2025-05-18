from xml import etree

import rdflib

from xsd_to_owl.auxiliary.uri_utils import lower_case_initial
from xsd_to_owl.core import XSDVisitor

# Define XML Schema namespace constant
XS_NS = "{http://www.w3.org/2001/XMLSchema}"


class DebugElementsRule(XSDVisitor):
    """
    Universal debugging rule to catch all elements and log them
    """

    @property
    def rule_id(self):
        return "debug_elements"

    @property
    def description(self):
        return "Debug all elements in the schema"

    @property
    def priority(self):
        return 1000  # Absolute highest priority

    def matches(self, element, context):
        # Print any element with 'AirBrake' in its name or type
        name = element.get('name')
        type_attr = element.get('type')

        if name and 'AirBrake' in name:
            print(f"DEBUG: Found element with name containing 'AirBrake': {name}, type: {type_attr}")
            print(f"Element tag: {element.tag}")
            parent = element.getparent()
            print(f"Parent tag: {parent.tag if parent else 'None'}")

        if type_attr and 'Numeric' in type_attr:
            print(f"DEBUG: Found element with Numeric type: name={name}, type={type_attr}")
            print(f"Element tag: {element.tag}")

        # Doesn't actually match anything - just for debugging
        return False

    def transform(self, element, context):
        # Never called since matches() always returns False
        return None


class ClassCreationDebugRule(XSDVisitor):
    """Debug rule to specifically track creation of problematic classes."""

    @property
    def rule_id(self):
        return "class_creation_debug"

    @property
    def description(self):
        return "Debug class creation"

    @property
    def priority(self):
        return 1001  # Higher than other debug rules

    def matches(self, element, context):
        # Only track specific classes
        name = element.get('name')
        if name == "AdministrativeDataSet":
            print(f"\n====== DEBUG: Found AdministrativeDataSet element ======")
            print(f"Element tag: {element.tag}")

            # Check what's already in the graph for this class name
            class_uri = context.get_safe_uri(context.base_uri, name)
            print(f"URI created: {class_uri}")

            # Check all triples with this class
            all_triples = []
            for s, p, o in context.graph.triples((class_uri, None, None)):
                all_triples.append((s, p, o))
                print(f"  Triple: {s} {p} {o}")

            for s, p, o in context.graph.triples((None, None, class_uri)):
                all_triples.append((s, p, o))
                print(f"  Triple: {s} {p} {o}")

            # Search for all triples with label=AdministrativeDataSet
            for s, p, o in context.graph.triples((None, context.RDFS.label, rdflib.Literal("AdministrativeDataSet"))):
                print(f"  Class with label: {s}")

            print("=================================================\n")

        # Don't actually match anything for transformation
        return False

    def transform(self, element, context):
        # Never called
        return None

    # Add to debug_rules.py


class URISanitizationDebugRule(XSDVisitor):
    """Debug rule to test URI sanitization."""

    @property
    def rule_id(self):
        return "uri_sanitization_debug"

    @property
    def description(self):
        return "Debug URI sanitization"

    @property
    def priority(self):
        return 1002  # Higher than other debug rules

    def matches(self, element, context):
        # Only for debugging specific class names
        name = element.get('name')
        if name == "AdministrativeDataSet":
            # Test URI sanitization for our problematic class
            from xsd_to_owl.auxiliary.uri_utils import sanitize_uri

            # Generate multiple URIs and check if they're the same
            sanitized1 = sanitize_uri(name, is_property=False)
            sanitized2 = sanitize_uri(name, is_property=False)

            print(f"\nURI Sanitization Test for {name}:")
            print(f"  First call: {sanitized1}")
            print(f"  Second call: {sanitized2}")
            print(f"  Same URI: {sanitized1 == sanitized2}")

            # Test the full URI generation
            uri1 = context.get_safe_uri(context.base_uri, name)
            uri2 = context.get_safe_uri(context.base_uri, name)

            print(f"  Full URI First call: {uri1}")
            print(f"  Full URI Second call: {uri2}")
            print(f"  Same URI: {uri1 == uri2}")

        # Don't actually match for transformation
        return False

    def transform(self, element, context):
        # Never called
        return None


# Add to debug_rules.py
class PropertyCreationDebugRule(XSDVisitor):
    """Debug rule to trace property creation process."""

    @property
    def rule_id(self):
        return "property_creation_debug"

    @property
    def description(self):
        return "Debug property creation"

    @property
    def priority(self):
        return 1001  # Higher than other debug rules

    def matches(self, element, context):
        # Only interested in elements that might become properties
        if element.tag != f"{XS_NS}element":
            return False

        # Get some basic info
        name = element.get('name')
        if name == "AdministrativeDataSet":
            print(f"\n====== PROPERTY CREATION DEBUG FOR {name} ======")

            # Get the actual is_datatype_property function
            from xsd_to_owl.auxiliary.property_utils import is_datatype_property as actual_func

            # Call and debug the actual function
            result = actual_func(element, name)
            print(f"Result from actual is_datatype_property: {result}")

            # Now test each step of the function
            complex_type = element.find(f"./{XS_NS}complexType")
            print(f"Direct complexType child lookup: {complex_type is not None}")

            print("=================================================\n")

        return False

    def transform(self, element, context):
        # Never called
        return None


class ComplexTypeDebugRule(XSDVisitor):
    """Debug rule to analyze complex type structures and their children."""

    @property
    def rule_id(self):
        return "complex_type_debug"

    @property
    def description(self):
        return "Debug complex type hierarchies"

    @property
    def priority(self):
        return 999  # Very high priority but not the highest

    def matches(self, element, context):
        # Only match specific elements we're interested in
        name = element.get('name')
        if name == "RollingStockDataSet":
            print(f"\n====== DEBUG: Found RollingStockDataSet element ======")
            print(f"Element tag: {element.tag}")

            # Check if this element has a complexType child
            complex_type = None
            for child in element:
                if child.tag == f"{XS_NS}complexType":
                    complex_type = child
                    print(f"  Found complexType child")
                    break

            if complex_type:
                # Look for sequence
                sequence = complex_type.find(f".//{XS_NS}sequence")
                if sequence:
                    print(f"  Found sequence in complexType")

                    # Check elements in sequence
                    for child in sequence.findall(f".//{XS_NS}element"):
                        child_name = child.get('name')
                        child_ref = child.get('ref')
                        child_type = child.get('type')
                        print(f"  Sequence element: {child_name or child_ref} (type: {child_type})")

                        # Check if this element has metadata
                        metadata = context.get_element_metadata(child)
                        print(f"  Has metadata: {metadata is not None}")
                        if metadata:
                            print(f"  Metadata: {metadata}")

            print("=================================================\n")

        return False  # Don't actually match for transformation

    def transform(self, element, context):
        # Never called
        return None


class SequenceElementDebugRule(XSDVisitor):
    """Debug rule to investigate sequence elements."""

    @property
    def rule_id(self):
        return "sequence_element_debug"

    @property
    def description(self):
        return "Debug sequence elements"

    @property
    def priority(self):
        return 999  # Very high priority

    def matches(self, element, context):
        # Only match sequence elements
        if element.tag != f"{XS_NS}sequence":
            return False

        # Get parent information
        parent = element.getparent()
        if parent is None:
            return False

        parent_tag = parent.tag
        parent_parent = parent.getparent()
        parent_parent_name = parent_parent.get('name') if parent_parent is not None else "None"

        print(f"\n====== DEBUG: Found sequence element ======")
        print(f"Parent tag: {parent_tag}")
        print(f"Grandparent name: {parent_parent_name}")

        # Count and show child elements
        child_count = 0
        for child in element:
            if child.tag == f"{XS_NS}element":
                child_name = child.get('name')
                child_ref = child.get('ref')
                child_type = child.get('type')
                print(f"  Child element: {child_name or child_ref} (type: {child_type})")

                # Show metadata
                metadata = context.get_element_metadata(child)
                if metadata:
                    print(f"  Child has metadata: {metadata}")
                else:
                    print(f"  Child has NO metadata")

                child_count += 1

        print(f"Total children: {child_count}")
        print("=================================================\n")

        # Don't actually match for transformation
        return False

    def transform(self, element, context):
        # Never called
        return None


class DetailedElementStructureDebugRule(XSDVisitor):
    """Debug rule to examine element structure in detail."""

    @property
    def rule_id(self):
        return "detailed_element_structure_debug"

    @property
    def description(self):
        return "Debug detailed element structure"

    @property
    def priority(self):
        return 1003  # Highest priority for debugging

    def matches(self, element, context):
        # Only match specific elements we're interested in
        name = element.get('name')
        if name == "AdministrativeDataSet":
            print(f"\n===== DETAILED ELEMENT STRUCTURE: {name} =====")
            print(f"Element tag: {element.tag}")
            print(f"Element attributes: {dict(element.attrib)}")

            # Check direct children
            print("\nDirect children:")
            for i, child in enumerate(element):
                print(f"  {i + 1}. Tag: {child.tag}, Attributes: {dict(child.attrib)}")

                # For complexType children, show their structure
                if child.tag == f"{XS_NS}complexType":
                    print("    ComplexType children:")
                    for j, grandchild in enumerate(child):
                        print(f"      {j + 1}. Tag: {grandchild.tag}, Attributes: {dict(grandchild.attrib)}")

                        # If there's a sequence, show its children too
                        if grandchild.tag == f"{XS_NS}sequence":
                            print("        Sequence children:")
                            for k, seq_child in enumerate(grandchild):
                                print(f"          {k + 1}. Tag: {seq_child.tag}, Attributes: {dict(seq_child.attrib)}")

            # Test the is_datatype_property function directly
            print("\nProperty type detection:")

            # Test direct complexType child check
            complex_child = element.find(f"./{XS_NS}complexType")
            print(f"  Direct complexType child: {complex_child is not None}")

            # Test deep simpleType search
            simple_child_deep = element.find(f".//{XS_NS}simpleType")
            print(f"  Deep simpleType search: {simple_child_deep is not None}")

            # Test direct simpleType child
            simple_child = element.find(f"./{XS_NS}simpleType")
            print(f"  Direct simpleType child: {simple_child is not None}")

            print("=================================================\n")

        return False  # Don't actually match for transformation

    def transform(self, element, context):
        # Never called
        return None


class PropertyTransformationTrackingRule(XSDVisitor):
    """Debug rule to track property transformations for specific elements."""

    @property
    def rule_id(self):
        return "property_transformation_tracking"

    @property
    def description(self):
        return "Track the transformation process for specific properties"

    @property
    def priority(self):
        return 74  # Just before ChildElementPropertyRule's priority of 75

    def matches(self, element, context):
        # Only match specific elements
        if element.tag != f"{XS_NS}element":
            return False

        name = element.get('name')
        if name == "AdministrativeDataSet":
            metadata = context.get_element_metadata(element)
            if metadata:
                print(f"\n====== PRE-TRANSFORMATION CHECK FOR {name} ======")
                print(f"Element will be processed by ChildElementPropertyRule next")
                print(f"Element metadata: {metadata}")

                # Comment out or remove the code that uses get_processed_rules
                # processed_by = []
                # for rule_id in context.get_processed_rules(element):
                #     processed_by.append(rule_id)
                # print(f"Already processed by: {processed_by}")
                print(f"Already processed by: [not available - get_processed_rules not implemented]")

                # Verify which property type it should be
                from xsd_to_owl.auxiliary.property_utils import is_datatype_property
                is_dt_prop = is_datatype_property(element, name)
                print(f"Should be a datatype property: {is_dt_prop}")
                print("=================================================\n")

        # Don't actually match anything for transformation
        return False

    def transform(self, element, context):
        # Never called
        return None


class ChildElementPropertyDebugRule(XSDVisitor):
    """Debug rule to trace child element processing."""

    @property
    def rule_id(self):
        return "child_element_property_debug"

    @property
    def description(self):
        return "Debug child element property creation"

    @property
    def priority(self):
        return 73  # Just before property creation

    def matches(self, element, context):
        if element.tag != f"{XS_NS}element":
            return False

        metadata = context.get_element_metadata(element)
        if metadata and 'parent_uri' in metadata:
            parent_name = metadata.get('parent_name', 'unknown')
            name = element.get('name') or element.get('ref')

            print(f"\n==== CHILD ELEMENT DEBUG: {name} of {parent_name} ====")
            print(f"Element attributes: {dict(element.attrib)}")
            print(f"Parent URI: {metadata['parent_uri']}")

            # Check if properties already exist
            property_name = lower_case_initial(name)
            property_uri = context.get_property_uri(property_name)
            if property_uri:
                print(f"Property already registered: {property_uri}")
                # Show triples
                for s, p, o in context.graph.triples((property_uri, None, None)):
                    print(f"  {s} {p} {o}")
            else:
                print(f"No property registered for {property_name}")

                # Check what is_datatype_property would return
                from xsd_to_owl.auxiliary.property_utils import is_datatype_property
                is_dt = is_datatype_property(element, name)
                print(f"Would be datatype property: {is_dt}")

            print("=============================================\n")

        return False

    def transform(self, element, context):
        return None


class PropertyCreationLifecycleRule(XSDVisitor):
    """Debug rule to track the complete lifecycle of property creation."""

    @property
    def rule_id(self):
        return "property_creation_lifecycle"

    @property
    def description(self):
        return "Track the complete lifecycle of property creation"

    @property
    def priority(self):
        return 1000  # Highest priority to see everything

    def matches(self, element, context):
        if element.tag != f"{XS_NS}element":
            return False

        # Focus on tracking all elements with metadata - these should become properties
        metadata = context.get_element_metadata(element)
        if metadata and 'parent_uri' in metadata:
            name = element.get('name') or element.get('ref')
            parent_name = metadata.get('parent_name', 'unknown')

            from xsd_to_owl.auxiliary.property_utils import is_datatype_property
            is_dt = is_datatype_property(element, name)

            print(f"\n==== PROPERTY LIFECYCLE: {name} (child of {parent_name}) ====")
            print(f"Should be datatype property: {is_dt}")

            # Check if there's already a class created for this element
            class_uri = context.get_safe_uri(context.base_uri, name)
            class_exists = (class_uri, context.RDF.type, context.OWL.Class) in context.graph
            print(f"Class exists: {class_exists}")

            # Check if there's a property for this element
            property_name = lower_case_initial(name)
            property_uri = context.get_property_uri(property_name)
            property_registered = property_uri is not None
            print(f"Property registered: {property_registered}")

            if property_registered:
                # Check if the property exists in the graph
                dt_prop_exists = (property_uri, context.RDF.type, context.OWL.DatatypeProperty) in context.graph
                obj_prop_exists = (property_uri, context.RDF.type, context.OWL.ObjectProperty) in context.graph
                print(f"DatatypeProperty exists: {dt_prop_exists}")
                print(f"ObjectProperty exists: {obj_prop_exists}")

            # Complex elements (should be object properties)
            complex_type = element.find(f"./{XS_NS}complexType")
            if complex_type is not None:
                print(f"Has complexType child - should be ObjectProperty")

                # Check if this element has been marked as processed
                if context.is_processed(element, "child_element_property"):
                    print(f"Element WAS processed by child_element_property rule")
                else:
                    print(f"Element was NOT processed by child_element_property rule")

            print("================================================\n")

        return False

    def transform(self, element, context):
        return None


class ComplexTypeChildMarkingDebugRule(XSDVisitor):
    """Debug rule to trace complex type child marking."""

    @property
    def rule_id(self):
        return "complex_type_child_marking_debug"

    @property
    def description(self):
        return "Debug complex type child marking"

    @property
    def priority(self):
        return 1000  # Very high priority for debugging

    def matches(self, element, context):
        if element.tag != f"{XS_NS}element":
            return False

        name = element.get('name')
        if name != "RollingStockDataset":
            return False

        print(f"\n==== DEBUG ROLLINGSTOCKDATASET PROCESSING ====")
        print(f"Element: {name}")
        print(
            f"Has been processed by anonymous_complex_type: {context.is_processed(element, 'anonymous_complex_type')}")

        # Find its complex type
        complex_type = None
        for child in element:
            if child.tag == f"{XS_NS}complexType":
                complex_type = child
                print(f"Found complexType child")
                break

        if complex_type is None:
            print(f"NO complexType child found!")
            return False

        # Find sequence
        sequence = complex_type.find(f"{XS_NS}sequence")
        if sequence is not None:
            print(f"Found direct sequence")

            # Count and list child elements
            children = sequence.findall(f"{XS_NS}element")
            print(f"Direct sequence has {len(children)} element children")

            # List each child
            for child in children:
                child_name = child.get('name')
                child_ref = child.get('ref')
                print(f"  Child: {child_name or child_ref}")

                # Check if this child has metadata
                metadata = context.get_element_metadata(child)
                if metadata:
                    print(f"  Child has metadata: {metadata}")
                else:
                    print(f"  Child has NO metadata")
        else:
            print(f"NO direct sequence found!")

        print("=======================================\n")
        return False

    def transform(self, element, context):
        return None


class ElementTypeAnalysisRule(XSDVisitor):
    """Debug rule to trace how element types are determined."""

    @property
    def rule_id(self):
        return "element_type_analysis"

    @property
    def description(self):
        return "Analyze how element types are determined"

    @property
    def priority(self):
        return 75  # Same as ChildElementPropertyRule

    def matches(self, element, context):
        if element.tag != f"{XS_NS}element":
            return False

        name = element.get('name')
        if name == "AdministrativeDataSet":
            print(f"\n==== ELEMENT TYPE ANALYSIS: {name} ====")

            # First check if this element has metadata
            metadata = context.get_element_metadata(element)
            if metadata:
                print(f"Element has parent metadata: {metadata}")
            else:
                print(f"Element has NO parent metadata")

            # Now check if it's been processed as a class
            class_uri = context.get_safe_uri(context.base_uri, name)
            is_class = (class_uri, context.RDF.type, context.OWL.Class) in context.graph
            print(f"Element exists as a class: {is_class}")

            # Now let's inspect how is_datatype_property would classify it
            from xsd_to_owl.auxiliary.property_utils import is_datatype_property

            # Store the result
            is_dt = is_datatype_property(element, name)
            print(f"is_datatype_property returns: {is_dt}")

            # Let's break down the function's logic step by step

            # 1. Check if the element has a type attribute
            has_type = element.get('type') is not None
            print(f"Element has 'type' attribute: {has_type}")

            # 2. Check if the element has a complexType child
            has_complex_child = element.find(f"{XS_NS}complexType") is not None
            print(f"Element has complexType child: {has_complex_child}")

            # 3. Check if there's a direct simpleType child
            has_simple_child = element.find(f"{XS_NS}simpleType") is not None
            print(f"Element has simpleType child: {has_simple_child}")

            # 4. Check for deep search for simpleType
            has_deep_simple = element.find(f".//{XS_NS}simpleType") is not None
            print(f"Element has nested simpleType: {has_deep_simple}")

            print("===========================================\n")

        return False

    def transform(self, element, context):
        return None


class RuleRegistrationDebugRule(XSDVisitor):
    """Debug rule to check if specific rules are registered and active."""

    @property
    def rule_id(self):
        return "rule_registration_debug"

    @property
    def description(self):
        return "Debug rule registration and activation"

    @property
    def priority(self):
        return 5  # Very low priority to run at the end

    def matches(self, element, context):
        # Only match once on the root element
        if element.tag.endswith("schema"):
            print("\n===== RULE REGISTRATION DEBUG =====")

            # Get the transformer's registry from the context (add as attribute before calling)
            if hasattr(context, 'transformer_registry'):
                registry = context.transformer_registry

                # List all registered rules
                print("Registered Rules:")
                for rule in registry.get_rules():
                    print(
                        f"  • {rule.rule_id} (Priority: {rule.priority}, Active: {rule.rule_id in registry._active_rules})")

                # Check specifically for child_element_property
                child_prop_rule = registry.get_rule_by_id("child_element_property")
                if child_prop_rule:
                    print("\nchild_element_property rule IS registered")
                    print(f"  Priority: {child_prop_rule.priority}")
                    print(f"  Active: {child_prop_rule.rule_id in registry._active_rules}")
                else:
                    print("\nchild_element_property rule is NOT registered!")
            else:
                print("ERROR: No transformer_registry available in context")

            print("====================================\n")
        return False

    def transform(self, element, context):
        return None


class DebugElementMetadataRule(XSDVisitor):
    """Debug rule to check element metadata."""

    @property
    def rule_id(self):
        return "debug_element_metadata"

    @property
    def description(self):
        return "Debug rule to check element metadata"

    @property
    def priority(self):
        return 350  # Higher than most rules to run first

    def matches(self, element, context):
        # Match specific elements we want to debug
        if element.tag != f"{XS_NS}element":
            return False

        name = element.get('name')
        ref = element.get('ref')

        # Only match AdministrativeDataSet or similar key elements
        debug_elements = ["AdministrativeDataSet"]
        return name in debug_elements or ref in debug_elements

    def transform(self, element, context):
        name = element.get('name') or element.get('ref')
        print(f"\n==== DEBUG METADATA FOR: {name} ====")

        # Print element details
        print(f"Element tag: {element.tag}")
        print(f"Element attributes: {element.attrib}")

        # Check if the element has parent metadata
        metadata = context.get_element_metadata(element)
        print(f"Has metadata: {metadata is not None}")
        if metadata:
            print(f"Metadata keys: {metadata.keys()}")
            if 'parent_name' in metadata:
                print(f"Parent name: {metadata['parent_name']}")
            if 'parent_uri' in metadata:
                print(f"Parent URI: {metadata['parent_uri']}")

        # Show element ID info
        element_id = etree.tostring(element)
        print(f"Element ID hash: {hash(element_id)}")

        # Check which rules have processed this element
        if element_id in context._processed_elements:
            print(f"Rules that processed this element: {context._processed_elements[element_id]}")
        else:
            print("No rules have processed this element yet")

        # Print the full serialized element for debugging
        print(f"Element full string (first 100 chars): {str(element_id)[:100]}...")

        # Don't actually do any transformation
        return None


class AnonymousTypeChildMarkingDebugRule(XSDVisitor):
    """Debug rule to track child element marking in AnonymousComplexTypeRule."""

    @property
    def rule_id(self):
        return "anonymous_complex_type_debug"

    @property
    def description(self):
        return "Debug child element marking in anonymous complex types"

    @property
    def priority(self):
        return 301  # Just after DetectSimpleTypeRule, before AnonymousComplexTypeRule

    def matches(self, element, context):
        # Match the same elements as AnonymousComplexTypeRule
        if element.tag != f"{XS_NS}element":
            return False

        if element.get('type') is not None:
            return False

        if element.get('name') is None:
            return False

        # Only match if it contains a complexType
        for child in element:
            if child.tag == f"{XS_NS}complexType":
                # Look for specific children we want to debug
                complex_type = child
                sequence = complex_type.find(f"{XS_NS}sequence") or complex_type.find(f".//{XS_NS}sequence")

                if sequence is not None:
                    for seq_child in sequence.findall(f"{XS_NS}element"):
                        child_name = seq_child.get('name')
                        child_ref = seq_child.get('ref')

                        # Check if the problematic element is a child
                        if child_name == "AdministrativeDataSet" or child_ref == "AdministrativeDataSet":
                            return True

                return False  # No sequence or no AdministrativeDataSet child

        return False

    def transform(self, element, context):
        name = element.get('name')
        print(f"\n==== DEBUG ANONYMOUS COMPLEX TYPE: {name} ====")

        # Create class URI for reference
        class_uri = context.get_safe_uri(context.base_uri, name)

        # Find child elements
        complex_type = None
        for child in element:
            if child.tag == f"{XS_NS}complexType":
                complex_type = child
                break

        if complex_type is None:
            print("No complexType child found (shouldn't happen)")
            return None

        print("Examining child elements:")

        # Find sequence
        sequence = complex_type.find(f"{XS_NS}sequence")
        if sequence is None:
            sequence = complex_type.find(f".//{XS_NS}sequence")

        if sequence is None:
            print("No sequence found in complex type")
            return None

        # Find and debug the AdministrativeDataSet element specifically
        for child in sequence.findall(f"{XS_NS}element"):
            child_name = child.get('name')
            child_ref = child.get('ref')

            if child_name == "AdministrativeDataSet" or child_ref == "AdministrativeDataSet":
                print(f"\nFound AdministrativeDataSet as child of {name}:")
                print(f"  Attributes: {child.attrib}")

                # Check existing metadata
                metadata = context.get_element_metadata(child)
                print(f"  Has metadata: {metadata is not None}")

                # Generate debug element ID info
                child_id = etree.tostring(child)
                print(f"  Child element ID hash: {hash(child_id)}")
                print(f"  Child element string (first 100 chars): {str(child_id)[:100]}...")

                # Try to manually add metadata
                context.add_element_metadata(child, {
                    'parent_name': name,
                    'parent_uri': class_uri,
                    'debug_added': True
                })

                # Check if metadata was added successfully
                metadata_after = context.get_element_metadata(child)
                print(f"  Metadata after manual add: {metadata_after is not None}")
                if metadata_after:
                    print(f"  Metadata keys after add: {metadata_after.keys()}")

                # Print details of metadata storage for all elements
                print("\nAll element metadata keys:")
                metadata_count = 0
                for key in context._element_metadata:
                    metadata_count += 1
                    if metadata_count <= 5:  # Limit to first 5 elements for brevity
                        print(f"  Key hash: {hash(key)}")
                        try:
                            el = etree.fromstring(key)
                            print(f"  Element: {el.tag} - name: {el.get('name')} - ref: {el.get('ref')}")
                        except:
                            print(f"  Could not parse key")

                print(f"  Total metadata entries: {metadata_count}")

        # Don't process this element further
        return None


class AdminDataSetDebugRule(XSDVisitor):
    """
    Debug rule to investigate specifically why AdministrativeDataSet isn't being processed
    by the child_element_property rule.
    """

    @property
    def rule_id(self):
        return "admin_data_set_debug"

    @property
    def description(self):
        return "Debug rule for AdministrativeDataSet property creation"

    @property
    def priority(self):
        return 70  # Run just before child_element_property rule (75)

    def matches(self, element, context):
        if element.tag != f"{XS_NS}element":
            return False

        name = element.get('name')
        ref = element.get('ref')

        if name == "AdministrativeDataSet" or ref == "AdministrativeDataSet":
            # Print detailed information about this element
            print(f"\n===== ADMIN DATA SET DEBUG =====")
            print(f"Element found: {name or ref}")
            print(f"Element attributes: {element.attrib}")

            # Check metadata and parent info
            metadata = context.get_element_metadata(element)
            print(f"Has parent metadata: {metadata is not None}")
            if metadata:
                print(f"Metadata contains: {list(metadata.keys())}")
                if 'parent_name' in metadata:
                    print(f"Parent name: {metadata['parent_name']}")
                if 'parent_uri' in metadata:
                    print(f"Parent URI: {metadata['parent_uri']}")

            # Check if this element has been processed already
            processed_rules = []
            element_id = context.get_element_id(element)
            if element_id in context._processed_elements:
                processed_rules = context._processed_elements[element_id]
            print(f"Processed by rules: {processed_rules}")

            # Check matching conditions for child_element_property rule
            from ..rules.property_rules import ChildElementPropertyRule
            child_rule = ChildElementPropertyRule()
            would_match = child_rule.matches(element, context)
            print(f"Would match child_element_property rule: {would_match}")

            # Check if property already exists
            property_name = "administrativeDataSet"
            from ..auxiliary.property_utils import get_registered_property
            existing = get_registered_property(property_name)
            print(f"Property '{property_name}' already exists: {existing is not None}")

            print("==================================")

            # We don't actually want to transform anything here
            return False

        return False

    def transform(self, element, context):
        # This should never be called due to returning False in matches
        return None

# AirBrakedMassLoadedDebugRule removed as it's no longer needed
