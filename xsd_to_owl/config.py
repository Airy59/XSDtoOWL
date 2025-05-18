# xsd_to_owl/config.py
"""
Configuration settings for the XSD to OWL transformation.
"""

# Default base URI for generated ontologies
DEFAULT_BASE_URI = "http://example.org/ontology#"

# XML Schema namespace
XS_NAMESPACE = "http://www.w3.org/2001/XMLSchema"
XS_PREFIX = "{" + XS_NAMESPACE + "}"

# Default rule configuration settings
DEFAULT_RULE_CONFIG = {
    "named_complex_type": True,
    "top_level_named_element": True,
    "anonymous_complex_type": True,
    "simple_type_property": True,
    "complex_type_reference": True,
    "named_enum_type": True,
    "anonymous_enum_type": True
}

# Default serialization format
DEFAULT_FORMAT = "turtle"

# Mapping of XSD simple types to XSD namespace URIs
XSD_SIMPLE_TYPE_MAPPING = {
    "string": "string",
    "boolean": "boolean",
    "decimal": "decimal",
    "float": "float",
    "double": "double",
    "duration": "duration",
    "dateTime": "dateTime",
    "time": "time",
    "date": "date",
    "gYearMonth": "gYearMonth",
    "gYear": "gYear",
    "gMonthDay": "gMonthDay",
    "gDay": "gDay",
    "gMonth": "gMonth",
    "hexBinary": "hexBinary",
    "base64Binary": "base64Binary",
    "anyURI": "anyURI",
    "QName": "QName",
    "NOTATION": "NOTATION",
    "integer": "integer",
    "positiveInteger": "positiveInteger",
    "negativeInteger": "negativeInteger",
    "nonNegativeInteger": "nonNegativeInteger",
    "nonPositiveInteger": "nonPositiveInteger",
    "long": "long",
    "unsignedLong": "unsignedLong",
    "int": "int",
    "unsignedInt": "unsignedInt",
    "short": "short",
    "unsignedShort": "unsignedShort",
    "byte": "byte",
    "unsignedByte": "unsignedByte"
}