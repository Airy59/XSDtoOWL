# xsd_to_owl/auxiliary/property_utils.py
import re
import rdflib
from xsd_to_owl.auxiliary.uri_utils import lower_case_initial
from xsd_to_owl.auxiliary.xsd_parsers import is_functional, get_documentation

# Constants
XS_NS = "{http://www.w3.org/2001/XMLSchema}"

# Property registry to track properties across transformation
_property_registry = {}  # Maps property names to their URIs and metadata


def reset_property_registry():
    """Reset the property registry when starting a new transformation."""
    global _property_registry
    _property_registry = {}


def register_property(property_name, property_uri, is_datatype=None):
    """
    Register a property in the registry.

    Args:
        property_name: The property name (without lowercasing)
        property_uri: The URI of the property
        is_datatype: Whether this is a datatype property (True) or object property (False)
    """
    property_name = lower_case_initial(property_name)
    _property_registry[property_name] = {
        'uri': property_uri,
        'is_datatype': is_datatype
    }


def get_registered_property(property_name):
    """
    Get a registered property URI if it exists.

    Args:
        property_name: The property name to look up

    Returns:
        Dict with 'uri' and 'is_datatype' keys or None if not found
    """
    property_name = lower_case_initial(property_name)
    return _property_registry.get(property_name)


def find_property_by_uri(uri):
    """Find a property name by its URI."""
    for name, data in _property_registry.items():
        if data['uri'] == uri:
            return name
    return None


def property_exists(property_uri, context):
    """Check if a property already exists in the graph."""
    return (property_uri, context.RDF.type, context.OWL.DatatypeProperty) in context.graph or \
        (property_uri, context.RDF.type, context.OWL.ObjectProperty) in context.graph


# def is_datatype_property(element, property_name=None):
#     """
#     Determine if an element should be represented as a datatype property.
#
#     Args:
#         element: The XML element to check
#         property_name: Optional property name for heuristic checks
#
#     Returns:
#         True if it should be a datatype property, False if it should be an object property
#     """
#     # Get existing registration if available
#     if property_name:
#         registered = get_registered_property(property_name)
#         if registered and registered['is_datatype'] is not None:
#             return registered['is_datatype']
#
#     # Check for complex type elements (which should be object properties)
#     if element.find(f"{XS_NS}complexType") is not None:
#         return False
#
#     # Check elements that are defined elsewhere and have a reference
#     ref = element.get('ref')
#     if ref:
#         # Look up the reference in the schema (element may be external)
#         try:
#             schema_root = element.getroottree().getroot()
#             referenced_element = find_referenced_element(element, ref, schema_root)
#             if referenced_element and referenced_element.find(f".//{XS_NS}complexType") is not None:
#                 return False
#         except:
#             # If we can't resolve the reference, use the other criteria
#             pass
#
#     # 1. Check for special case types
#     type_attr = element.get('type')
#     special_types = ["AirBrakedMassLoaded"]
#     if type_attr and (type_attr.startswith('Numeric') or element.get('name') in special_types):
#         return True
#
#     # 2. Check for built-in XSD types
#     if type_attr and ':' in type_attr:  # xs:string, xs:dateTime, etc.
#         return True
#
#     # 3. Check for inline simpleType
#     if element.find(f".//{XS_NS}simpleType") is not None:
#         return True
#
#     # 4. Check for simple content inside complex type
#     if element.find(f".//{XS_NS}simpleContent") is not None:
#         return True
#
#     # 5. Heuristic check based on property name
#     if property_name:
#         date_time_keywords = ["date", "time", "timestamp", "validity", "expiry", "until", "since"]
#         if any(keyword in property_name.lower() for keyword in date_time_keywords):
#             return True
#
#     # For elements that reference a known type, check if that type is a class
#     if type_attr and not (':' in type_attr):
#         # This is a reference to a type defined in the schema
#         # By default, we'll assume this is an object property unless one of the
#         # above criteria identified it as a datatype property
#         return False
#
#     # Default to object property if we're not sure
#     return False


def is_datatype_property(element, property_name):
    """Determine if the element should create a datatype property."""
    # First check special cases
    from xsd_to_owl.config.special_cases import is_forced_datatype_property, should_never_be_object_property
    
    # Get element name (either from name attribute or property_name)
    element_name = element.get('name') or property_name
    
    # Get element type
    element_type = element.get('type')
    
    # If it's in the special cases, respect that decision
    if element_name and (is_forced_datatype_property(element_name) or should_never_be_object_property(element_name, element_type)):
        return True
    
    # Debug for sandwich elements
    if property_name == "AdministrativeDataSet":
        print(f"\n==== PROPERTY TYPE CHECK: {property_name} ====")

        # Check complex type directly
        complex_direct = element.find(f"./{XS_NS}complexType") is not None
        print(f"Direct complexType: {complex_direct}")

        # Check complex type recursively
        complex_deep = element.find(f".//{XS_NS}complexType") is not None
        print(f"Deep complexType: {complex_deep}")

        # Check simple type directly
        simple_direct = element.find(f"./{XS_NS}simpleType") is not None
        print(f"Direct simpleType: {simple_direct}")

        # Check simple type recursively
        simple_deep = element.find(f".//{XS_NS}simpleType") is not None
        print(f"Deep simpleType: {simple_deep}")

        # Check type attribute
        type_attr = element.get('type')
        print(f"Type attribute: {type_attr}")

        # Final decision
        is_dt = not (complex_direct or (type_attr and 'simple' not in type_attr.lower()))
        print(f"Decision - is datatype property: {is_dt}")
        print("=====================================")

    # Check for numeric types
    type_attr = element.get('type')
    if type_attr and (type_attr.startswith('Numeric') or re.match(r'^Numeric\d+(-\d+)?$', type_attr)):
        return True

    # Regular logic (unchanged)
    has_complex_type = element.find(f"./{XS_NS}complexType") is not None
    has_type_attr = element.get('type') is not None

    # If it has a complex type child, it's not a datatype property
    if has_complex_type:
        return False

    # If it has a type attribute and it's not a simple type, it's not a datatype property
    if has_type_attr and 'simple' not in element.get('type').lower():
        return False

    # Otherwise, assume it's a datatype property
    return True


def determine_datatype_range(element, property_name, context):
    """
    Determine the appropriate range for a datatype property.

    Args:
        element: The XML element
        property_name: The property name
        context: The transformation context

    Returns:
        URI of the appropriate XSD datatype
    """
    type_attr = element.get('type')

    # Check numeric types
    if type_attr and type_attr.startswith('Numeric'):
        return context.XSD.decimal

    # Check explicit XSD type reference
    if type_attr and ':' in type_attr:
        return context.get_type_reference(type_attr)

    # Use heuristics for date/time properties
    if property_name and any(term in property_name.lower() for term in ["date", "time", "expiry", "until", "since"]):
        return context.XSD.dateTime

    # Default to string for other simple types
    return context.XSD.string


def find_referenced_element(element, ref_name, schema_root):
    """Find an element referenced by 'ref' attribute."""
    if not ref_name:
        return None

    ref_elements = schema_root.findall(f".//*[@name='{ref_name}']")
    return ref_elements[0] if ref_elements else None


def create_datatype_property(property_uri, property_name, parent_uri, range_uri, element, context):
    """Create a datatype property in the graph."""
    context.graph.add((property_uri, context.RDF.type, context.OWL.DatatypeProperty))
    context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(property_name)))
    if parent_uri:
        context.graph.add((property_uri, context.RDFS.domain, parent_uri))
    context.graph.add((property_uri, context.RDFS.range, range_uri))

    # Add functional property if appropriate
    if is_functional(element):
        context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

    # Add documentation if available
    doc = get_documentation(element)
    if doc:
        context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc, lang="en")))

    # Register in our property registry
    register_property(property_name, property_uri, is_datatype=True)

    return property_uri


def create_object_property(property_uri, property_name, parent_uri, target_name, element, context):
    """Create an object property in the graph."""
    # Get or create the target class
    target_class_uri = context.get_safe_uri(context.base_uri, target_name)

    # Ensure target class exists
    if (target_class_uri, context.RDF.type, context.OWL.Class) not in context.graph:
        context.graph.add((target_class_uri, context.RDF.type, context.OWL.Class))
        context.graph.add((target_class_uri, context.RDFS.label, rdflib.Literal(target_name)))
        context.graph.add((target_class_uri, context.RDFS.comment,
                           rdflib.Literal(f"Auto-generated class for property {property_name}")))

    # Create the property
    context.graph.add((property_uri, context.RDF.type, context.OWL.ObjectProperty))
    context.graph.add((property_uri, context.RDFS.label, rdflib.Literal(property_name)))
    if parent_uri:
        context.graph.add((property_uri, context.RDFS.domain, parent_uri))
    context.graph.add((property_uri, context.RDFS.range, target_class_uri))

    # Add property characteristics
    if is_functional(element):
        context.graph.add((property_uri, context.RDF.type, context.OWL.FunctionalProperty))

    # Add documentation if available
    doc = get_documentation(element)
    if doc:
        context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc, lang="en")))

    # Register in our property registry
    register_property(property_name, property_uri, is_datatype=False)

    return property_uri


def enhance_existing_property(property_uri, element, parent_uri, context):
    """
    Enhance an existing property with additional information.

    Args:
        property_uri: The URI of the existing property
        element: The current element with potential additional info
        parent_uri: The domain URI to add if missing
        context: The transformation context

    Returns:
        The property URI
    """
    # Check if property already has a domain
    has_domain = False
    for _, _, o in context.graph.triples((property_uri, context.RDFS.domain, None)):
        has_domain = True
        break

    # Add domain if missing and parent_uri is provided
    if not has_domain and parent_uri:
        context.graph.add((property_uri, context.RDFS.domain, parent_uri))
        print(f"  Added domain to existing property: {property_uri}")

    # Check if property already has documentation
    has_doc = False
    for _, _, o in context.graph.triples((property_uri, context.SKOS.definition, None)):
        has_doc = True
        break

    # Add documentation if missing
    if not has_doc:
        doc = get_documentation(element)
        if doc:
            context.graph.add((property_uri, context.SKOS.definition, rdflib.Literal(doc, lang="en")))
            print(f"  Added documentation to existing property: {property_uri}")

    return property_uri


def get_property_uri_for_name(property_name, context, is_property=True):
    """
    Get the URI for a property by name, checking registry first.

    Args:
        property_name: The property name
        context: The transformation context
        is_property: Whether this is a property (for URI construction)

    Returns:
        The property URI
    """
    # Normalize property name
    property_name = lower_case_initial(property_name)

    # Check registry first
    registered = get_registered_property(property_name)
    if registered:
        return registered['uri']

    # If not in registry, generate a new URI
    return context.get_safe_uri(context.base_uri, property_name, is_property=is_property)
