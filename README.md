# Purpose

Transpose XSD to RDF/OWL in view of further transformations (OWL to OWL)

# Rationale

XSDs define, as the initialism tells, schemas, i.e. document structures, and are not easily mapped to a sensible ontology. Mapping tools can deal with the syntax, not the semantics, with poor results. This is probably the reason why such mapping tools are not easily found. For instance, TopBraid Composer (Maestro Edition) had such capability, but has been phased out. Other dedicated tools have changed focus.

# Methodology

Transformation shall be deterministic, based on rules that can be activated and de-activated (user setting).

# Means

Transformation could be indirect, e.g. over UML (using XSD to UML mapping provided by Enterprise Architect or similar tools, then UML to OWL). Here, we chose to avoid such indirections, although the possibility of editing the resulting class diagram to make it look more like a conceptual model was appealing. The downside is, transformation would no longer be deterministic.

We experimented with different tools, such as XSLT, Python (with libraries), SWI PROLOG... (not all are documented here).

Given the small size of XSDs and small number of variants to be transformed, execution time or memory footprint are not of concern.

In this situation, none of the more exotic tools showed decisive advantages over Python, not even conciseness (Python has great libraries, which helps), so we sticked with Python.

For testing purposes, the transformation code was applied to the TAF TSI XSD, version 3.5. The file is publicly available, and copied here for convenience. It is long and complex enough to serve as a test case.

# License

Code: EUPL 1.2
XSD files: depending on source.

# Status

As of May 18, 2025:

* the rule-based transformation basically works.
* the set of rules is not complete.
  * multiplicities are not transformed yet (except 0..1 that translates to owl:FunctionalProperty); generation of SHACL shapes should be envisaged here;
  * some XSD terms might not yet be taken into account.
* no user interface is yet available to select rules or groups of rules. Such tuning currently implies editing a .py file.

# Usage

## Command Line Conversion

To convert XSD files to OWL ontologies from the command line, use the `transform_GCU_RSDS.py` script. Below are example commands for common use cases:

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

### Available Options

- `--xsd-path`: Path to the XSD file(s) (can be specified multiple times)
- `--base-uri`: Base URI for the ontology (default: "http://example.org/ontology#")
- `--uri-encode`: Method to encode URIs with spaces (choices: "percent", "underscore", "camelcase", "dash", "plus"; default: "underscore")
- `--output`: Path to save the output file (default: auto-generated based on input filename)
- `--format`: Output format (choices: "turtle", "xml", "n3", "nt", "json-ld", "nquads", "trig"; default: "turtle")
- `--log-level`: Logging level (choices: "debug", "info", "warning", "error"; default: "info")
