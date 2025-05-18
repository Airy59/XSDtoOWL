# XSD to OWL Transformation Framework

## Introduction

This framework provides a flexible and extensible solution for transforming XML Schema Definition (XSD) documents into
Web Ontology Language (OWL) and Simple Knowledge Organization System (SKOS) ontologies.
It enables automated conversion between XML-based data models and semantic web representations,
facilitating interoperability between different data ecosystems.

## Features

- Transformation of XSD complex types to OWL classes
- Conversion of XSD elements to OWL properties
- Support for XSD enumerations as SKOS concept schemes
- Handling of xs:choice elements using OWL constraints
- Customizable transformation rules
- Extensible architecture for custom transformations
- Multiple output formats (Turtle, RDF/XML, N3, etc.)

## Installation

### Requirements

- Python 3.13+
- Required packages:
  - `lxml>=5.4.0` - XML/XSD parser
  - `rdflib>=7.1.4` - Ontology library
  - `click>=8.2.0` - Command-line interface implementation
  - `networkx>=3.4.2` - For handling complex XSD structures using graph reasoning

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Airy59/XSDtoOWL.git
   cd XSDtoOWL
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```python
from xsd_to_owl import create_taf_cat_transformer

# Create a transformer with TAF CAT specific rules
transformer = create_taf_cat_transformer()

# Transform an XSD file to OWL
input_xsd = "Input_xsd/taf_cat_complete.xsd"  # or an XML string
base_uri = "http://example.org/ontology#"
graph = transformer.transform(input_xsd, base_uri)

# Save the result
output_file = "Output_owl/output_taf_cat_complete_ontology.ttl"
transformer.save(graph, output_file, format="turtle")
```

### Command Line Interface

The framework provides a command-line interface through the `transform_TAF_CAT.py` script:

```bash
python transform_TAF_CAT.py --xsd-path Input_xsd/taf_cat_complete.xsd
```

Additional options:
```bash
python transform_TAF_CAT.py \
  --xsd-path Input_xsd/taf_cat_complete.xsd \
  --base-uri "http://example.org/ontology#" \
  --uri-encode underscore \
  --output my_ontology.ttl \
  --format turtle \
  --log-level info
```

If no output is specified, the result will be saved to `Output_owl/output_[filename]_ontology.ttl` in the project root directory.

## Architecture

The XSD to OWL transformation framework follows a rule-based architecture, where each rule handles a specific aspect of
the XSD schema.

### Core Components

1. **Transformer**: The main class that orchestrates the transformation process.
2. **Rule**: Abstract class that defines the interface for transformation rules.
3. **Pipeline**: Manages the execution of rules in phases.
4. **Context**: Maintains state and provides utilities during transformation.

### Default Rules

The framework includes the following default rules:

1. **ComplexTypeRule**: Transforms XSD complex types into OWL classes.
2. **ElementRule**: Transforms XSD elements into OWL properties.
3. **AttributeRule**: Transforms XSD attributes into OWL datatype properties.
4. **EnumerationRule**: Transforms XSD enumerations into SKOS concept schemes.
5. **SimpleTypeRule**: Transforms XSD simple types into OWL datatypes.
6. **ChoiceElementPropertyRule**: Transforms XSD choice elements into OWL properties with constraints.

## Customization

### Creating Custom Rules

You can create custom rules by extending the `BaseRule` class:

```python
from xsd_to_owl.rules.base import BaseRule

class MyCustomRule(BaseRule):
    @property
    def rule_id(self):
        return "my_custom_rule"
        
    @property
    def description(self):
        return "Custom rule for specialized XSD patterns"
        
    def matches(self, element, context):
        # Your matching logic here
        return element.tag.endswith('mySpecialElement')
        
    def transform(self, element, context):
        # Your transformation logic here
        uri = context.create_uri(element.get('name'))
        context.graph.add((uri, context.RDF.type, context.OWL.Class))
```

### Configuring the Transformer

You can register custom rules with the transformer:

```python
from xsd_to_owl import XSDtoOWLTransformer
from my_custom_rules import MyCustomRule

# Create a transformer
transformer = XSDtoOWLTransformer()

# Register custom rules
transformer.register_rule(MyCustomRule())
```

### Handling xs:choice Elements

The framework provides a specialized rule for handling xs:choice elements in XSD schemas. The `ChoiceElementPropertyRule` transforms xs:choice elements into a set of OWL properties with constraints to ensure that exactly one of the properties is used.

#### XML Schema xs:choice Semantics

In XML Schema, the xs:choice element specifies that exactly one of the elements contained in the group may appear in the containing element. This creates a mutual exclusivity constraint that must be preserved in the OWL representation.

#### Approaches

The framework supports two approaches for handling xs:choice elements, depending on the types of elements in the choice:

##### Approach 1: For Simple Types

For xs:choice elements containing elements of simple type or numeric type, the approach is based on OWL disjointness and cardinality constraints:

1. Each option in the choice is represented as a separate property
2. All properties share the same domain (the parent class)
3. Each property has a range corresponding to its type
4. Comments are added to each property to indicate that it's part of a choice constraint
5. Unicity constraints are implied through documentation, as OWL does not directly support mutual exclusivity between properties

This approach is particularly well-suited for choices between elements of simple type or numeric type, as it maintains the mutual exclusivity constraint of xs:choice while working within OWL's capabilities.

To enforce the unicity constraint in applications consuming the ontology, additional validation rules would need to be implemented, as standard OWL reasoners cannot enforce the constraint that exactly one of several properties must be used.

##### Approach 2: For Complex Types

For xs:choice elements containing elements of complex type, a class hierarchy approach is more appropriate:

1. Create a superclass as the property range with the naming pattern: `<containing element name>_choice_<disambiguation digit>`
2. Make all choice options subclasses of that superclass
3. Create a single object property with the superclass as its range
4. Each subclass represents one option in the choice
5. Add owl:disjointWith assertions between all subclasses to enforce mutual exclusivity
6. Add owl:FunctionalProperty assertion to the object property to enforce that exactly one instance is used

This approach provides a more elegant solution for complex types, as it leverages OWL's class hierarchy to represent the choice constraint. The unicity constraint (exactly one choice must be selected) is enforced through the combination of:
- Disjoint subclasses (ensuring no instance can be of more than one choice type)
- Functional property (ensuring exactly one instance of the superclass is used)

Example:

```turtle
:PaymentType a owl:Class ;
    rdfs:label "PaymentType" .

:paymentMethod a owl:ObjectProperty, owl:FunctionalProperty ;
    rdfs:domain :PaymentType ;
    rdfs:range :PaymentType_choice_1 ;
    rdfs:label "paymentMethod" .

:PaymentType_choice_1 a owl:Class ;
    rdfs:label "PaymentType_choice_1" ;
    rdfs:comment "Superclass for xs:choice options" .

:CreditCardType a owl:Class ;
    rdfs:subClassOf :PaymentType_choice_1 ;
    rdfs:label "CreditCardType" ;
    owl:disjointWith :BankTransferType, :PayPalType .

:BankTransferType a owl:Class ;
    rdfs:subClassOf :PaymentType_choice_1 ;
    rdfs:label "BankTransferType" ;
    owl:disjointWith :CreditCardType, :PayPalType .

:PayPalType a owl:Class ;
    rdfs:subClassOf :PaymentType_choice_1 ;
    rdfs:label "PayPalType" ;
    owl:disjointWith :CreditCardType, :BankTransferType .
```

#### Implementation

To use the xs:choice handling in your transformer:

```python
from xsd_to_owl import create_default_transformer
from xsd_to_owl.rules.property_rules import ChoiceElementPropertyRule

# Create a transformer
transformer = create_default_transformer()

# Register the ChoiceElementPropertyRule
transformer.register_rule(ChoiceElementPropertyRule(), 'property')
```

The TAF CAT transformer already includes this rule by default.

## Examples

### Transform XSD Complex Type to OWL Class

XSD:
```xml
<xs:complexType name="PersonType">
    <xs:sequence>
        <xs:element name="firstName" type="xs:string"/>
        <xs:element name="lastName" type="xs:string"/>
        <xs:element name="age" type="xs:integer" minOccurs="0"/>
    </xs:sequence>
</xs:complexType>
```

Resulting OWL (Turtle syntax):

```turtle
:PersonType a owl:Class ;
    rdfs:label "PersonType" ;
    rdfs:comment "Complex type from XSD schema" .

:firstName a owl:DatatypeProperty ;
    rdfs:domain :PersonType ;
    rdfs:range xsd:string ;
    rdfs:label "firstName" .

:lastName a owl:DatatypeProperty ;
    rdfs:domain :PersonType ;
    rdfs:range xsd:string ;
    rdfs:label "lastName" .

:age a owl:DatatypeProperty ;
    rdfs:domain :PersonType ;
    rdfs:range xsd:integer ;
    rdfs:label "age" .
```

### Transform XSD Enumeration to SKOS Concept Scheme

XSD:

```xml
<xs:simpleType name="CountryCode">
    <xs:restriction base="xs:string">
        <xs:enumeration value="US"/>
        <xs:enumeration value="UK"/>
        <xs:enumeration value="FR"/>
        <xs:enumeration value="DE"/>
    </xs:restriction>
</xs:simpleType>
```

Resulting SKOS (Turtle syntax):

```turtle
:CountryCode a skos:ConceptScheme ;
    rdfs:label "CountryCode" ;
    rdfs:comment "Enumeration from XSD schema" .

:CountryCode_US a skos:Concept ;
    skos:inScheme :CountryCode ;
    skos:prefLabel "US" .

:CountryCode_UK a skos:Concept ;
    skos:inScheme :CountryCode ;
    skos:prefLabel "UK" .

:CountryCode_FR a skos:Concept ;
    skos:inScheme :CountryCode ;
    skos:prefLabel "FR" .

:CountryCode_DE a skos:Concept ;
    skos:inScheme :CountryCode ;
    skos:prefLabel "DE" .
```

### Transform XSD Choice to OWL Properties with Constraints

XSD:

```xml
<xs:complexType name="PaymentType">
    <xs:sequence>
        <xs:choice>
            <xs:element name="creditCard" type="CreditCardType"/>
            <xs:element name="bankTransfer" type="BankTransferType"/>
            <xs:element name="paypal" type="PayPalType"/>
        </xs:choice>
    </xs:sequence>
</xs:complexType>
```

Resulting OWL (Turtle syntax):

```turtle
:PaymentType a owl:Class ;
    rdfs:label "PaymentType" ;
    rdfs:comment "Complex type from XSD schema" .

:creditCard a owl:ObjectProperty ;
    rdfs:domain :PaymentType ;
    rdfs:range :CreditCardType ;
    rdfs:label "creditCard" ;
    rdfs:comment "This represents an xs:choice element with 3 options. Exactly one of these properties must be used." .

:bankTransfer a owl:ObjectProperty ;
    rdfs:domain :PaymentType ;
    rdfs:range :BankTransferType ;
    rdfs:label "bankTransfer" ;
    rdfs:comment "This represents an xs:choice element with 3 options. Exactly one of these properties must be used." .

:paypal a owl:ObjectProperty ;
    rdfs:domain :PaymentType ;
    rdfs:range :PayPalType ;
    rdfs:label "paypal" ;
    rdfs:comment "This represents an xs:choice element with 3 options. Exactly one of these properties must be used." .
```

## Transformation Rules

The framework applies the following transformation rules:

| XSD Construct | OWL/SKOS Representation        |
|---------------|--------------------------------|
| Complex Type  | OWL Class                      |
| Element       | OWL Object/Datatype Property   |
| Attribute     | OWL Datatype Property          |
| Enumeration   | SKOS Concept Scheme + Concepts |
| Simple Type   | OWL Datatype                   |
| Extension     | rdfs:subClassOf relationship   |
| Restriction   | OWL Restrictions               |
| Choice        | OWL Properties with constraints|

## Rule Priority Management

The transformation framework employs a priority-based system to resolve conflicts when multiple rules match the same XSD
element. This ensures deterministic and predictable transformations, particularly when dealing with ambiguous XSD
structures.

### Priority System

- Each rule has a priority value, with higher values indicating higher priority.
- The default priority (100) is defined in the base `XSDVisitor` class.
- Rules only need to override this value when they require a non-default priority.
- When multiple rules match an element, only the rule with the highest priority is applied.

### Priority Bands

The framework uses the following priority bands to organize rules logically:

| Priority Range | Rule Category                    | Description                                                                                             |
|----------------|----------------------------------|---------------------------------------------------------------------------------------------------------|
| 150-200        | Specialized High-Priority Rules  | Rules for special cases that should take precedence over standard rules (e.g., NumericTypePropertyRule) |
| 100-149        | Standard Datatype Property Rules | Rules for converting elements to datatype properties                                                    |
| 50-99          | Object Property Rules            | Rules for converting elements to object properties                                                      |
| 1-49           | Fallback/Catch-all Rules         | Generic rules that should only apply when no other rules match                                          |

### Example

For instance, when processing an element like `AirBrakeMassLoaded`, both a datatype property rule (priority 100) and an
object property rule (priority 50) might match. The priority system ensures that only the datatype property rule is
applied, avoiding the creation of duplicate or conflicting properties.

### Benefits

- **Deterministic Transformation**: The same input always produces the same output, regardless of rule execution order.
- **Clean Resolution of Ambiguities**: Clear handling of XSD elements that could be interpreted in multiple ways.
- **Extensibility**: New rules can be added at appropriate priority levels without disrupting existing rules.
- **Maintainability**: The priority system makes the transformation process more transparent and easier to reason about.

## Output Configuration

The framework supports various output formats using rdflib serialization:

- Turtle (`format="turtle"`)
- RDF/XML (`format="xml"`)
- N-Triples (`format="nt"`)
- JSON-LD (`format="json-ld"`)
- N3 (`format="n3"`)
- NQuads (`format="nquads"`)
- TriG (`format="trig"`)

## Best Practices

1. **Base URI Selection**: Choose a meaningful base URI that reflects your domain.
2. **Reuse Existing Ontologies**: Where appropriate, connect your transformed ontology with existing ones.
3. **Post-Processing**: Consider manual refinement of the generated ontology for better semantic clarity.
4. **Versioning**: Include version information in your ontology URI.
5. **URI Encoding**: Choose an appropriate URI encoding method for handling spaces and special characters.

## Troubleshooting

### Common Issues

1. **XML Parsing Errors**:
    - Ensure your XSD is well-formed
    - For UTF-8 encoded XML strings, convert to bytes before parsing

2. **Namespace Issues**:
    - Check that namespace prefixes in the XSD are properly handled
    - Ensure base URI ends with # or /

3. **Circular References**:
    - The framework detects and handles circular references in XSD

4. **Inconsistent Property Types**:
    - The framework includes post-processing to fix properties that are both datatype and object properties
    - Configure special cases in xsd_to_owl/config/special_cases.py

## Observations about the output files

### No domain?

You may notice that some properties have no domain:
- This is formally acceptable, in RDF/OWL. It does not prevent using the property; the only consequence is, no inference can be made about the individual having that property (apart being an instance of owl:Thing like any OWL individual).
- Such cases occur when elements are defined at the top level in the XSD schema, but referenced nowhere. Such an orphaned element is not good practice, and might be a leftover from previous versions.

## Future Development

- Support for more advanced XSD features
- Integration with ontology alignment tools
- Bidirectional transformation (OWL to XSD)
- Performance optimizations for large schemas
- User interface for rule selection and configuration
- Support for SHACL shapes generation for multiplicities

## Contributing

Contributions are welcome! Here are some ways you can contribute to the project:

1. Report bugs and suggest features by creating issues
2. Submit pull requests with bug fixes or new features
3. Improve documentation
4. Create additional transformation rules for specialized XSD constructs

## License

Code: EUPL 1.2
XSD files: depending on source.