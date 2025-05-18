"""
URI utilities for XSD to OWL/RDF transformation.

This module provides functions for handling and sanitizing URIs during the
transformation process from XSD schemas to OWL/RDF ontologies.
"""

from typing import Optional, Set

# Constants for URI encoding methods
URI_ENCODE_UNDERSCORE = "underscore"
URI_ENCODE_CAMELCASE = "camelcase"
URI_ENCODE_PERCENT = "percent"
URI_ENCODE_DASH = "dash"
URI_ENCODE_PLUS = "plus"

# Tracking for unique URI fragments
_used_class_identifiers: Set[str] = set()
_used_property_identifiers: Set[str] = set()
_used_other_identifiers: Set[str] = set()



def reset_uri_tracking():
    """
    Reset the tracking of used URIs.
    Call this at the beginning of a new transformation to clear any previous state.
    """
    global _used_class_identifiers, _used_property_identifiers, _used_other_identifiers
    _used_class_identifiers = set()
    _used_property_identifiers = set()
    _used_other_identifiers = set()



def lower_case_initial(s: str) -> str:
    if s and s[0].isalpha():
        return s[0].lower() + s[1:]
    else:
        return s


def sanitize_uri(name: str, is_property: bool = False, identifier_set: Optional[Set[str]] = None) -> str:
    """
    Sanitize a name for use as a URI fragment.

    Args:
        name: The raw name to sanitize
        is_property: If True, ensures the first character is lowercase (for properties)
        identifier_set: Optional custom set to track used identifiers
                       (defaults to module-level tracking)

    Returns:
        A sanitized URI fragment that is valid and unique
    """
    # Use the provided set or select the appropriate tracking set
    if identifier_set is not None:
        used_ids = identifier_set
    else:
        if is_property:
            used_ids = _used_property_identifiers
        else:
            # For class names, we want to REUSE the same identifier if it's the same name
            # So we'll just check if it exists for debugging but won't add a counter
            # We still track it in _used_class_identifiers for tracking purposes
            used_ids = _used_class_identifiers

    if not isinstance(name, str):
        return f"unnamed_{len(used_ids)}"

    # Remove XML namespace if present
    if "{" in name and "}" in name:
        name = name.split('}')[-1]

    # Replace invalid characters with underscores
    sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)

    # For properties, ensure the first character is lowercase
    if is_property:
        sanitized = lower_case_initial(sanitized)

    # KEY CHANGE: Only add uniqueness suffixes for properties, not for classes
    # This ensures the same class name always gets the same URI
    if is_property:
        original = sanitized
        counter = 1
        while sanitized in used_ids:
            sanitized = f"{original}_{counter}"
            counter += 1

    # Register the new identifier
    used_ids.add(sanitized)
    return sanitized



def normalize_enum_name(name: str) -> str:
    """
    Normalize an enumeration name to a consistent form.

    Args:
        name: The raw enumeration name

    Returns:
        A normalized version of the name with a consistent suffix
    """
    if not name:
        return name

    # Strip common suffixes
    suffix_patterns = ['_enum', 'enum', 'Enum', '_Enum']
    for suffix in suffix_patterns:
        if name.endswith(suffix):
            name = name[:-len(suffix)]

    # Add a consistent suffix
    return f"{name}_enum"


def encode_uri_fragment(text: str, method: str = URI_ENCODE_UNDERSCORE) -> str:
    """
    Encode a string using the specified method for URI construction.

    Args:
        text: The text to encode
        method: The encoding method:
               - 'underscore': Replace spaces with underscores
               - 'camelcase': Convert to camelCase
               - 'percent': Use percent encoding
               - 'dash': Replace spaces with dashes
               - 'plus': Replace spaces with plus signs

    Returns:
        An encoded URI fragment
    """
    if not text:
        return text

    if method == URI_ENCODE_UNDERSCORE:
        return text.replace(' ', '_')

    elif method == URI_ENCODE_CAMELCASE:
        words = text.split()
        if not words:
            return text
        result = words[0].lower()
        for word in words[1:]:
            if word:
                result += word[0].upper() + word[1:].lower()
        return result

    elif method == URI_ENCODE_PERCENT:
        import urllib.parse
        return urllib.parse.quote(text)

    elif method == URI_ENCODE_DASH:
        return text.replace(' ', '-')

    elif method == URI_ENCODE_PLUS:
        return text.replace(' ', '+')

    # Default to underscore if method not recognized
    return text.replace(' ', '_')


def get_local_name(uri_or_curie: str) -> str:
    """
    Extract the local name (fragment) from a URI or CURIE.

    Args:
        uri_or_curie: A URI or CURIE string

    Returns:
        The local name part
    """
    if '#' in uri_or_curie:
        return uri_or_curie.split('#')[-1]
    elif '/' in uri_or_curie:
        return uri_or_curie.split('/')[-1]
    elif ':' in uri_or_curie:
        return uri_or_curie.split(':')[-1]
    return uri_or_curie
