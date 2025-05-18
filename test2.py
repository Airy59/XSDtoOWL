import rdflib

from xsd_to_owl.rules.class_rules import NamedComplexTypeRule, TopLevelNamedElementRule, AnonymousComplexTypeRule
from xsd_to_owl.rules.enum_rules import NamedEnumTypeRule, AnonymousEnumTypeRule
from xsd_to_owl.rules.property_rules import SimpleTypePropertyRule, ComplexTypeReferenceRule
# Import the classes directly
from xsd_to_owl.transform import XSDtoOWLTransformer

# Create a simple XSD schema as a string
sample_xsd = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    
    <!-- A named complex type -->
    <xs:complexType name="PersonType">
        <xs:annotation>
            <xs:documentation>Represents a person</xs:documentation>
        </xs:annotation>
        <xs:sequence>
            <xs:element name="firstName" type="xs:string"/>
            <xs:element name="lastName" type="xs:string"/>
            <xs:element name="age" type="xs:integer" minOccurs="0"/>
            <xs:element name="address" type="AddressType" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Another named complex type -->
    <xs:complexType name="AddressType">
        <xs:sequence>
            <xs:element name="street" type="xs:string"/>
            <xs:element name="city" type="xs:string"/>
            <xs:element name="country" type="CountryCode"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- A named enum type -->
    <xs:simpleType name="CountryCode">
        <xs:restriction base="xs:string">
            <xs:enumeration value="US"/>
            <xs:enumeration value="CA"/>
            <xs:enumeration value="UK"/>
        </xs:restriction>
    </xs:simpleType>
    
    <!-- A top-level element with type reference -->
    <xs:element name="Person" type="PersonType"/>
    
    <!-- A top-level element with anonymous complex type -->
    <xs:element name="Organization">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="name" type="xs:string"/>
                <xs:element name="headquarters" type="AddressType"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
    
</xs:schema>
"""


def create_transformer():
    """
    Create a transformer with all default rules registered.

    Returns:
        XSDtoOWLTransformer: A transformer with all default rules
    """
    transformer = XSDtoOWLTransformer()

    # Register all default rules
    transformer.register_rule(NamedComplexTypeRule())
    transformer.register_rule(TopLevelNamedElementRule())
    transformer.register_rule(AnonymousComplexTypeRule())
    transformer.register_rule(SimpleTypePropertyRule())
    transformer.register_rule(ComplexTypeReferenceRule())
    transformer.register_rule(NamedEnumTypeRule())
    transformer.register_rule(AnonymousEnumTypeRule())

    return transformer


# Create a test function
def test_transformation():
    # Create a transformer with all default rules
    transformer = create_transformer()

    # Set the base URI for the ontology
    base_uri = "http://example.org/ontology#"

    # Transform the XSD to OWL
    try:
        graph = transformer.transform(sample_xsd, base_uri)

        # Print some statistics
        print(f"Transformation successful!")
        print(f"Number of triples: {len(graph)}")

        # Count types of resources
        classes = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Class)))
        datatype_props = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.DatatypeProperty)))
        object_props = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty)))
        concept_schemes = len(list(graph.subjects(rdflib.RDF.type, rdflib.SKOS.ConceptScheme)))
        concepts = len(list(graph.subjects(rdflib.RDF.type, rdflib.SKOS.Concept)))

        print(f"OWL Classes: {classes}")
        print(f"Datatype Properties: {datatype_props}")
        print(f"Object Properties: {object_props}")
        print(f"SKOS Concept Schemes: {concept_schemes}")
        print(f"SKOS Concepts: {concepts}")

        # Serialize to Turtle format
        turtle = graph.serialize(format="turtle")
        print("\nSample of the generated ontology (in Turtle format):")
        print(turtle[:1000] + "...")  # Print just the beginning

        # Save to file
        with open("output_ontology.ttl", "w") as f:
            f.write(turtle)
        print("\nFull ontology saved to 'output_ontology.ttl'")

        return True
    except Exception as e:
        print(f"Transformation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Run the test
if __name__ == "__main__":
    test_transformation()
