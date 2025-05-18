import os
import rdflib

# Import the create_taf_cat_transformer function
from xsd_to_owl import create_taf_cat_transformer

# Add the parent directory to the path if needed
# sys.path.append(os.path.abspath('..'))

# Create a simple XSD schema as a string
sample_xsd = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    
    <!-- A named complex type -->
    <xs:complexType name="PersonType">
        <xs:annotation>
            <xs:documentation>Represents a person</xs:documentation>
        </xs:annotation>
        <xs:sequence>
            <xs:element name="firstName" type="xs:string">
                <xs:annotation>
                    <xs:documentation>Person's first name</xs:documentation>
                </xs:annotation>
            </xs:element>
            <xs:element name="lastName" type="xs:string">
                <xs:annotation>
                    <xs:documentation>Person's last name</xs:documentation>
                </xs:annotation>
            </xs:element>
            <xs:element name="age" type="xs:integer" minOccurs="0">
                <xs:annotation>
                    <xs:documentation>Person's age in years</xs:documentation>
                </xs:annotation>
            </xs:element>
            <xs:element name="address" type="AddressType" minOccurs="0">
                <xs:annotation>
                    <xs:documentation>Person's address</xs:documentation>
                </xs:annotation>
            </xs:element>
            <xs:element name="status" minOccurs="0">
                <xs:annotation>
                    <xs:documentation>Person's current status</xs:documentation>
                </xs:annotation>
                <xs:simpleType>
                    <xs:restriction base="xs:string">
                        <xs:enumeration value="active">
                            <xs:annotation>
                                <xs:documentation>Person is currently active</xs:documentation>
                            </xs:annotation>
                        </xs:enumeration>
                        <xs:enumeration value="inactive">
                            <xs:annotation>
                                <xs:documentation>Person is currently inactive</xs:documentation>
                            </xs:annotation>
                        </xs:enumeration>
                        <xs:enumeration value="pending">
                            <xs:annotation>
                                <xs:documentation>Person's status is pending review</xs:documentation>
                            </xs:annotation>
                        </xs:enumeration>
                    </xs:restriction>
                </xs:simpleType>
            </xs:element>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Another named complex type -->
    <xs:complexType name="AddressType">
        <xs:annotation>
            <xs:documentation>Represents a physical address</xs:documentation>
        </xs:annotation>
        <xs:sequence>
            <xs:element name="street" type="xs:string"/>
            <xs:element name="city" type="xs:string"/>
            <xs:element name="state" type="xs:string"/>
            <xs:element name="postalCode" type="xs:string"/>
            <xs:element name="country" type="CountryCode"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- A named enum type -->
    <xs:simpleType name="CountryCode">
        <xs:annotation>
            <xs:documentation>ISO country codes</xs:documentation>
        </xs:annotation>
        <xs:restriction base="xs:string">
            <xs:enumeration value="US">
                <xs:annotation>
                    <xs:documentation>United States</xs:documentation>
                </xs:annotation>
            </xs:enumeration>
            <xs:enumeration value="CA">
                <xs:annotation>
                    <xs:documentation>Canada</xs:documentation>
                </xs:annotation>
            </xs:enumeration>
            <xs:enumeration value="UK">
                <xs:annotation>
                    <xs:documentation>United Kingdom</xs:documentation>
                </xs:annotation>
            </xs:enumeration>
            <xs:enumeration value="FR">
                <xs:annotation>
                    <xs:documentation>France</xs:documentation>
                </xs:annotation>
            </xs:enumeration>
        </xs:restriction>
    </xs:simpleType>
    
    <!-- A top-level element with type reference -->
    <xs:element name="Person" type="PersonType">
        <xs:annotation>
            <xs:documentation>A person record</xs:documentation>
        </xs:annotation>
    </xs:element>
    
    <!-- A top-level element with anonymous complex type -->
    <xs:element name="Organization">
        <xs:annotation>
            <xs:documentation>An organization record</xs:documentation>
        </xs:annotation>
        <xs:complexType>
            <xs:sequence>
                <xs:element name="name" type="xs:string"/>
                <xs:element name="headquarters" type="AddressType"/>
                <xs:element name="yearFounded" type="xs:integer"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
    
</xs:schema>
"""


def test_transformation():
    # Create a transformer with all default rules
    transformer = create_taf_cat_transformer()

    # Set the base URI for the ontology
    base_uri = "http://example.org/ontology#"

    # Transform the XSD to OWL
    try:
        graph = transformer.transform(sample_xsd.encode('utf-8'), base_uri)

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

        # Create Output_owl directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Output_owl')
        os.makedirs(output_dir, exist_ok=True)

        # Define output file path
        output_file = os.path.join(output_dir, "test_output.ttl")

        # Serialize to Turtle format
        turtle = graph.serialize(format="turtle")
        print("\nSample of the generated ontology (in Turtle format):")
        print(turtle[:1000] + "...")  # Print just the beginning

        # Save to file
        with open(output_file, "w") as f:
            f.write(turtle)
        print(f"\nFull ontology saved to '{output_file}'")

        return True
    except Exception as e:
        print(f"Transformation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Run the test
if __name__ == "__main__":
    test_transformation()
