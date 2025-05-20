# XML to RDF Transformation Module

## Introduction

This module provides functionality to convert XML data to RDF data using an OWL ontology that was generated from the corresponding XSD schema. It extends the XSD to OWL transformation framework by enabling the conversion of actual XML instance data to RDF triples that conform to the generated ontology.

## Features

- Transformation of XML elements to RDF resources
- Conversion of XML attributes to RDF properties
- Handling of XML element hierarchies as RDF object properties
- Support for XML element text content as RDF datatype properties
- Mapping of XML enumeration values to SKOS concepts
- Multiple output formats (Turtle, RDF/XML, N3, etc.)

## Usage

### Basic Usage

```python
from xml_to_rdf import create_default_converter

# Create a converter
converter = create_default_converter(base_uri="http://example.org/data#")

# Convert XML to RDF
xml_file = "Input_xml/taf_cat_example.xml"
owl_ontology = "Output_owl/taf_cat_codelists_ontology.ttl"
graph = converter.convert(xml_file, owl_ontology)

# Save the result
output_file = "Output_rdf/taf_cat_example_rdf.ttl"
converter.save(graph, output_file, format="turtle")
```

### Command Line Interface

The module provides a command-line interface through the `transform_xml_to_rdf.py` script:

```bash
python transform_xml_to_rdf.py --xml-path Input_xml/taf_cat_example.xml --owl-path Output_owl/taf_cat_codelists_ontology.ttl
```

Additional options:
```bash
python transform_xml_to_rdf.py \
  --xml-path Input_xml/taf_cat_example.xml \
  --owl-path Output_owl/taf_cat_codelists_ontology.ttl \
  --base-uri "http://example.org/data#" \
  --output my_data.ttl \
  --format turtle \
  --log-level info
```

If no output is specified, the result will be saved to `Output_rdf/[filename]_rdf.ttl` in the project root directory.

## Architecture

The XML to RDF transformation module follows a similar architecture to the XSD to OWL transformation framework, with a focus on mapping XML elements to RDF resources based on the OWL ontology.

### Core Components

1. **Converter**: The main class that orchestrates the transformation process.
2. **Mapping**: Manages the mapping between XML elements and OWL classes/properties.
3. **Rules**: (Future enhancement) Will provide customizable transformation rules.

## Transformation Process

The transformation process involves the following steps:

1. **Load the OWL ontology**: The ontology generated from the XSD schema is loaded into memory.
2. **Initialize the mapping**: The mapping between XML elements and OWL classes/properties is initialized based on the ontology.
3. **Parse the XML data**: The XML data is parsed into a tree structure.
4. **Process the XML elements**: Each XML element is processed recursively, creating RDF resources and properties based on the mapping.
5. **Generate the RDF graph**: The RDF triples are added to a graph.
6. **Serialize the RDF data**: The RDF graph is serialized to the specified format.

## Mapping Strategy

The mapping between XML and RDF follows these general rules:

1. **XML elements** with complex content are mapped to **RDF resources** (instances of OWL classes).
2. **XML elements** with simple content are mapped to **RDF datatype properties**.
3. **XML attributes** are mapped to **RDF datatype properties**.
4. **XML element hierarchies** are mapped to **RDF object properties**.
5. **XML enumeration values** are mapped to **SKOS concepts**.

## Example

### XML Input

```xml
<taf:AirBrakeType xmlns:taf="http://www.era.europa.eu/schemes/TAFTSI/3.5">3</taf:AirBrakeType>
```

### RDF Output (Turtle)

```turtle
@prefix base: <http://example.org/data#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

base:AirBrakeType_123456 rdf:type <http://example.org/ontology#AirBrakeType> ;
    base:value "3"^^xsd:string .
```

## Future Enhancements

- Support for more complex XML structures
- Rule-based transformation customization
- Bidirectional transformation (RDF to XML)
- Performance optimizations for large XML files
- Integration with SHACL validation

## Related Modules

- **xsd_to_owl**: Transforms XSD schemas to OWL ontologies
- **transform_TAF_CAT.py**: Command-line script for XSD to OWL transformation
- **transform_xml_to_rdf.py**: Command-line script for XML to RDF transformation