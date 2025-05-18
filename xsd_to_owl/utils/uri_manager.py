# xsd_to_owl/utils/uri_manager.py
"""
Centralized URI management for XSD to OWL transformation.
Provides consistent URI generation and tracking across all components.
"""

import urllib.parse
from typing import Dict, Optional, Set

import rdflib
from rdflib import URIRef, Namespace

from xsd_to_owl.utils import logging

# Constants for URI encoding methods
URI_ENCODE_UNDERSCORE = "underscore"
URI_ENCODE_CAMELCASE = "camelcase"
URI_ENCODE_PERCENT = "percent"
URI_ENCODE_DASH = "dash"
URI_ENCODE_PLUS = "plus"


class URIManager:
    """
    Centralized manager for URI generation and tracking.
    Ensures consistent URI creation and prevents duplicates.
    """
    
    def __init__(self, base_uri: str, encoding_method: str = URI_ENCODE_UNDERSCORE):
        """
        Initialize a new URI manager.
        
        Args:
            base_uri: The base URI for generated resources
            encoding_method: Method to encode URIs with spaces
        """
        # Ensure base_uri ends with # or /
        if not base_uri.endswith('#') and not base_uri.endswith('/'):
            base_uri += '#'
            
        self.base_uri = Namespace(base_uri)
        self.encoding_method = encoding_method
        
        # Track URIs to ensure uniqueness
        self._class_uris: Dict[str, URIRef] = {}
        self._property_uris: Dict[str, URIRef] = {}
        self._concept_uris: Dict[str, URIRef] = {}
        
        # Track used local names to avoid conflicts
        self._used_class_names: Set[str] = set()
        self._used_property_names: Set[str] = set()
        self._used_concept_names: Set[str] = set()
        
        logging.debug(f"Initialized URI manager with base URI '{base_uri}' and encoding method '{encoding_method}'")
    
    def get_class_uri(self, name: str) -> URIRef:
        """
        Get or create a URI for a class.
        
        Args:
            name: The name of the class
            
        Returns:
            A URI reference for the class
        """
        # Check if we already have a URI for this class
        if name in self._class_uris:
            return self._class_uris[name]
        
        # Create a new URI
        safe_name = self._sanitize_name(name, is_property=False)
        uri = self.base_uri[safe_name]
        
        # Store for future reference
        self._class_uris[name] = uri
        self._used_class_names.add(safe_name)
        
        logging.debug(f"Created class URI: {uri} for name '{name}'")
        return uri
    
    def get_property_uri(self, name: str, is_datatype: bool = True) -> URIRef:
        """
        Get or create a URI for a property.
        
        Args:
            name: The name of the property
            is_datatype: Whether this is a datatype property (affects logging only)
            
        Returns:
            A URI reference for the property
        """
        # Normalize property names to lowercase initial
        normalized_name = self._lower_case_initial(name)
        
        # Check if we already have a URI for this property
        if normalized_name in self._property_uris:
            return self._property_uris[normalized_name]
        
        # Create a new URI
        safe_name = self._sanitize_name(normalized_name, is_property=True)
        uri = self.base_uri[safe_name]
        
        # Store for future reference
        self._property_uris[normalized_name] = uri
        self._used_property_names.add(safe_name)
        
        prop_type = "datatype" if is_datatype else "object"
        logging.debug(f"Created {prop_type} property URI: {uri} for name '{name}'")
        return uri
    
    def get_concept_uri(self, scheme_uri: URIRef, value: str) -> URIRef:
        """
        Create a URI for a SKOS concept based on its scheme URI and value.
        
        Args:
            scheme_uri: URI of the concept scheme
            value: The enumeration value
            
        Returns:
            URI for the concept
        """
        # Create a unique key for this concept
        key = f"{scheme_uri}_{value}"
        
        # Check if we already have a URI for this concept
        if key in self._concept_uris:
            return self._concept_uris[key]
        
        # Extract the local name from the scheme URI
        scheme_local = str(scheme_uri).split('#')[-1]
        
        # Create a concept URI by appending the value to the scheme local name
        concept_local = f"{scheme_local}_{value}"
        safe_name = self._sanitize_name(concept_local, is_property=False)
        
        # Get the base part of the URI
        base_part = str(scheme_uri).split('#')[0] + '#'
        
        # Create the full concept URI
        uri = URIRef(base_part + safe_name)
        
        # Store for future reference
        self._concept_uris[key] = uri
        
        logging.debug(f"Created concept URI: {uri} for value '{value}' in scheme {scheme_uri}")
        return uri
    
    def _sanitize_name(self, name: str, is_property: bool = False) -> str:
        """
        Sanitize a name for use in a URI.
        
        Args:
            name: The name to sanitize
            is_property: Whether this is a property name (affects casing)
            
        Returns:
            A sanitized name suitable for use in a URI
        """
        if not name:
            return "unnamed"
        
        # Remove XML namespace if present
        if "{" in name and "}" in name:
            name = name.split('}')[-1]
        
        # Replace invalid characters with underscores
        sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        
        # For properties, ensure the first character is lowercase
        if is_property:
            sanitized = self._lower_case_initial(sanitized)
        
        # Encode according to the configured method
        encoded = self._encode_uri_fragment(sanitized)
        
        # Ensure uniqueness if needed
        if is_property:
            registry = self._used_property_names
        else:
            registry = self._used_class_names
        
        # Add a suffix if needed to ensure uniqueness
        if encoded in registry and encoded != sanitized:
            counter = 1
            while f"{encoded}_{counter}" in registry:
                counter += 1
            encoded = f"{encoded}_{counter}"
        
        return encoded
    
    def _encode_uri_fragment(self, text: str) -> str:
        """
        Encode a string using the specified method for URI construction.
        
        Args:
            text: The text to encode
            
        Returns:
            An encoded URI fragment
        """
        if not text:
            return text
        
        if self.encoding_method == URI_ENCODE_UNDERSCORE:
            return text.replace(' ', '_')
        
        elif self.encoding_method == URI_ENCODE_CAMELCASE:
            words = text.split()
            if not words:
                return text
            result = words[0].lower()
            for word in words[1:]:
                if word:
                    result += word[0].upper() + word[1:].lower()
            return result
        
        elif self.encoding_method == URI_ENCODE_PERCENT:
            return urllib.parse.quote(text)
        
        elif self.encoding_method == URI_ENCODE_DASH:
            return text.replace(' ', '-')
        
        elif self.encoding_method == URI_ENCODE_PLUS:
            return text.replace(' ', '+')
        
        # Default to underscore if method not recognized
        return text.replace(' ', '_')
    
    @staticmethod
    def _lower_case_initial(s: str) -> str:
        """
        Convert the first character of a string to lowercase.
        
        Args:
            s: The string to convert
            
        Returns:
            The string with the first character in lowercase
        """
        if s and s[0].isalpha():
            return s[0].lower() + s[1:]
        return s