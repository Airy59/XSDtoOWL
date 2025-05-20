"""
XML to RDF transformation module.

This module provides functionality to convert XML data to RDF data
using an OWL ontology that was generated from the corresponding XSD schema.
"""

from xml_to_rdf.converter import XMLtoRDFConverter, create_default_converter

__all__ = ['XMLtoRDFConverter', 'create_default_converter']