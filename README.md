# Purpose
## XSD to OWL...

Transpose XSD to RDF/OWL in view of further transformations (OWL to OWL), and convert XML data to RDF using the generated OWL ontologies.

XSDs are document models - lots of structures, little semantics. Changing the syntax to RDF/OWL will not turn an XSD into an ontology, but that's a first step. This project also provides functionality to convert XML data (conforming to an XSD schema) to RDF data using the OWL ontology generated from the XSD.

## XML to RDF...
The next obvious step is to allow transforming an XML file into RDF (A-Box), assuming that the XSD underpinning the XML file has an RDF/OWL equivalent (T-Box).

At least one open-source project proposed a solution here, see [Ontmalizer](https://github.com/srdc/ontmalizer?tab=readme-ov-file), the existence of which I discovered too late.

Please note that [RML](https://rml.io/specs/rml/) does the data transformation job, but requires the mapping to be input by the user. The difference here is, the mapping is generated, and is project-independent.

# Rationale

XSDs define, as the initialism tells, schemas, i.e. document structures, and are not easily mapped to a sensible ontology. Mapping tools can deal with the syntax, not the semantics, with poor results. This is probably the reason why such mapping tools are not easily found. For instance, TopBraid Composer (Maestro Edition) had such capability, but has been phased out. Other dedicated tools have changed focus.

# Methodology

Transformation shall be deterministic, based on rules that can be activated and de-activated (user setting).

# Means

Transformation could be indirect, e.g. over UML (using XSD to UML mapping provided by Enterprise Architect or similar tools, then UML to OWL). Here, we chose to avoid such indirections, although the possibility of editing the resulting class diagram to make it look more like a conceptual model was appealing. The downside is, transformation would no longer be deterministic.

We experimented with different tools, such as XSLT, Python (with libraries), SWI PROLOG... (not all are documented here).

Given the small size of XSDs and small number of variants to be transformed, execution time or memory footprint are not of concern.

In this situation, none of the more exotic tools showed decisive advantages over Python, not even conciseness (Python has great libraries, which helps), so we sticked with Python.

# License

Code: EUPL 1.2
XSD files: depending on source.

# Status

As of May 18, 2025:

* the rule-based XSD to OWL transformation basically works.
* the set of rules is not complete.
  * multiplicities are not transformed yet (except 0..1 that translates to owl:FunctionalProperty); generation of SHACL shapes should be envisaged here;
  * some XSD terms (such as xs:choice) are not taken into account,
* the XML to RDF transformation is now available, allowing conversion of XML data to RDF using the generated OWL ontologies.
* no user interface is yet available to select rules or groups of rules. Such tuning currently implies editing a .py file.

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

# Architecture

The project consists of two main modules:

1. **xsd_to_owl**: Transforms XSD schemas to OWL ontologies
2. **xml_to_rdf**: Transforms XML data to RDF using the generated OWL ontologies

## XSD to OWL Module

The XSD to OWL transformation framework follows a rule-based architecture, where each rule handles a specific aspect of the XSD schema. See the `xsd_to_owl/Documentation.md` file for detailed information.

## XML to RDF Module

The XML to RDF transformation module uses the OWL ontology generated from the XSD schema to transform XML data to RDF. It maps XML elements to RDF resources based on the classes and properties defined in the ontology. See the `xml_to_rdf/README.md` file for detailed information.

# Transformation Process

## XSD to OWL Transformation

1. Parse the XSD schema
2. Apply transformation rules to create OWL classes, properties, and SKOS concepts
3. Generate the OWL ontology
4. Serialize the ontology to the specified format

## XML to RDF Transformation

1. Load the OWL ontology generated from the XSD schema
2. Parse the XML data
3. Map XML elements to RDF resources based on the ontology
4. Generate the RDF graph
5. Serialize the RDF data to the specified format

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

# License

Code: EUPL 1.2
XSD files: depending on source.
