# Purpose

Transpose XSD to RDF/OWL (T-Box) in view of further transformations (OWL to OWL).

Transform XML data to RDF (A-Box) using the matching XSD and RDF/OWL T-Box as input parameters.

# Rationale

XSDs define, as the initialism tells, schemas, i.e. document structures, and are not easily mapped to a sensible ontology. Mapping tools can deal with the syntax, not the semantics, with poor results. This is probably the reason why such mapping tools are not easily found. For instance, TopBraid Composer (Maestro Edition) had such capability, but has been phased out. Other dedicated tools have changed focus.

There is at least (and probably at most) one open source project on GitHub that achieves the same goals, namely [Ontmalizer](https://github.com/srdc/ontmalizer), the existence of which I found too late. It uses Java code.

Please note that [RML](https://rml.io/specs/rml/) provides XML-to-RDF transformation, but the mapping rules must be provided by the user, for each particular project. In the present case, the mapping rules are provided by the software and apply at model level.

# Methodology

Transformation shall be deterministic, based on rules that can be activated and de-activated (user setting).

# Means
## Existing solutions?
Transformation could be indirect, e.g. over UML (using XSD to UML mapping provided by Enterprise Architect or similar tools, then UML to OWL). Here, we chose to avoid such indirections, although the possibility of editing the resulting class diagram to make it look more like a conceptual model was appealing. The downside is, transformation would no longer be deterministic.

We experimented with different tools, such as XSLT, Python (with libraries), SWI PROLOG... (not all are documented here).

Given the small size of XSDs and small number of variants to be transformed, execution time or memory footprint are not of concern.

In this situation, none of the more exotic tools showed decisive advantages over Python, not even conciseness (Python has great libraries, which helps), so we sticked with Python.
## What about RML?
[RML](https://rml.io/) allows to map XML data to RDF data via a graph that must be composed "manually". It is well suited to cases where the source XSD and the target ontology already exist.

By contrast, our proposed solution is designed for cases where the target ontology does not exist, or needs considerable extensions. In such case, the target ontology is derived from the source XSD, and data transformation can follow. Both model and data transformation can be automated.

# License

Code: EUPL 1.2
XSD files: depending on source.

# Status

As of May 20, 2025:

* the rule-based XSD to OWL transformation basically works.
  * the set of rules is not complete.
    * multiplicities are not transformed yet (except 0..1 that translates to owl:FunctionalProperty); generation of SHACL shapes should be envisaged here.
  * simple user interface (pre-defined terminal prompts)
* the XML to RDF transformation entirely rests on the correspondence between the XSD and the OWL ontology generated from the XSD.
  * extensive tests pending
  * user-defined transformation rules are foreseen but not implemented.

# Usage

## XSD to OWL Conversion

To convert XSD files to OWL ontologies from the command line, use the `transform_TAF_CAT.py` script. Below are example commands for common use cases:

### Basic Conversion

Convert a single XSD file to OWL (Turtle format):

```bash
python transform_TAF_CAT.py --xsd-path Input_xsd/taf_cat_complete.xsd
```

The output will be saved to `Output_owl/output_gcu_rsds_ontology.ttl` by default.

### Multiple Input Files

Convert multiple XSD files and merge them into a single ontology:

```bash
python transform_TAF_CAT.py --xsd-path Input_xsd/taf_cat_complete.xsd --xsd-path Input_xsd/gcu_wdr.xsd
```

The merged output will be saved to `Output_owl/merged_rsds_ontology.ttl`.

### Custom Output Path and Format

Specify a custom output path and format:

```bash
python transform_TAF_CAT.py --xsd-path Input_xsd/taf_cat_complete.xsd --output my_ontology.rdf --format xml
```

### All Options

```bash
python transform_TAF_CAT.py \
  --xsd-path Input_xsd/taf_cat_complete.xsd \
  --base-uri "http://example.org/ontology#" \
  --uri-encode underscore \
  --output my_ontology.ttl \
  --format turtle \
  --log-level info
```

### Available Options for XSD to OWL

- `--xsd-path`: Path to the XSD file(s) (can be specified multiple times)
- `--base-uri`: Base URI for the ontology (default: "http://example.org/ontology#")
- `--uri-encode`: Method to encode URIs with spaces (choices: "percent", "underscore", "camelcase", "dash", "plus"; default: "underscore")
- `--output`: Path to save the output file (default: auto-generated based on input filename)
- `--format`: Output format (choices: "turtle", "xml", "n3", "nt", "json-ld", "nquads", "trig"; default: "turtle")
- `--log-level`: Logging level (choices: "debug", "info", "warning", "error"; default: "info")

## XML to RDF Conversion

To convert XML data to RDF using the generated OWL ontologies, use the `transform_xml_to_rdf.py` script:

```bash
python transform_xml_to_rdf.py --xml-path Input_xml/taf_cat_example.xml --owl-path Output_owl/taf_cat_codelists_ontology.ttl
```

### Available Options for XML to RDF

- `--xml-path`: Path to the XML file
- `--owl-path`: Path to the OWL ontology file
- `--base-uri`: Base URI for the RDF data (default: "http://example.org/data#")
- `--output`: Path to save the output file (default: auto-generated based on input filename)
- `--format`: Output format (choices: "turtle", "xml", "n3", "nt", "json-ld", "nquads", "trig"; default: "turtle")
- `--log-level`: Logging level (choices: "debug", "info", "warning", "error"; default: "info")

# Transformation Process

## XSD to OWL Transformation

The XSD to OWL transformation process follows these steps:

1. Parse the XSD schema
2. Apply transformation rules to create OWL classes, properties, and SKOS concepts
3. Generate the OWL ontology
4. Serialize the ontology to the specified format

The transformation follows these general mapping principles:

- XSD complex types → OWL classes
- XSD elements → OWL properties
- XSD attributes → OWL datatype properties
- XSD enumerations → SKOS concept schemes

## XML to RDF Transformation

The XML to RDF transformation process follows these steps:

1. Load the OWL ontology generated from the XSD schema
2. Parse the XML data
3. Map XML elements to RDF resources based on the ontology
4. Generate the RDF graph
5. Serialize the RDF data to the specified format

### XML to RDF Mapping Principles

The XML to RDF transformation relies on the OWL ontology generated by the XSD to OWL transformation. The mapping follows these principles:

1. **XSD complex types → OWL classes → RDF resources**: XML elements corresponding to XSD complex types are mapped to instances of the corresponding OWL classes.
2. **XSD elements → OWL properties → RDF properties**: XML element relationships are mapped to RDF properties based on the OWL properties generated from XSD element declarations.
3. **XSD attributes → OWL datatype properties → RDF datatype properties**: XML attributes are mapped to RDF datatype properties.
4. **XSD enumerations → SKOS concept schemes → SKOS concepts**: XML enumeration values are mapped to SKOS concepts.

The mapping uses lexical correspondence between names in the XML document and identifiers in the OWL ontology, ensuring that the RDF data accurately reflects the structure and semantics defined in the XSD schema.

# Examples

## Example 1: Transform XSD to OWL

```bash
python transform_TAF_CAT.py --xsd-path Input_xsd/taf_cat_codelists.xsd
```

## Example 2: Transform XML to RDF

```bash
python transform_xml_to_rdf.py --xml-path Input_xml/taf_cat_example.xml --owl-path Output_owl/taf_cat_codelists_ontology.ttl
```

## Example 3: Programmatic Usage

```python
# Step 1: Transform XSD to OWL
from xsd_to_owl import create_taf_cat_transformer

transformer = create_taf_cat_transformer()
ontology = transformer.transform("Input_xsd/taf_cat_codelists.xsd")
transformer.save(ontology, "Output_owl/taf_cat_codelists_ontology.ttl")

# Step 2: Transform XML to RDF
from xml_to_rdf import create_default_converter

converter = create_default_converter()
rdf_graph = converter.convert("Input_xml/taf_cat_example.xml", "Output_owl/taf_cat_codelists_ontology.ttl")
converter.save(rdf_graph, "Output_rdf/taf_cat_example_rdf.ttl")
```

# Future Development

- Support for more advanced XSD features
- Integration with ontology alignment tools
- Bidirectional transformation (OWL to XSD, RDF to XML)
- Performance optimizations for large schemas and XML files
- User interface for rule selection and configuration
- Support for SHACL shapes generation for multiplicities
- Enhanced XML to RDF mapping with customizable rules

# Contributing

Contributions are welcome! Here are some ways you can contribute to the project:

1. Report bugs and suggest features by creating issues
2. Submit pull requests with bug fixes or new features
3. Improve documentation
4. Create additional transformation rules for specialized XSD constructs
5. Provide sample XSDs and sample data for testing, especially "borderline cases".

# License

Code: EUPL 1.2
XSD and XML files: depending on source.
