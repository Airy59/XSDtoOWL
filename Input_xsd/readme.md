The source files in this repository were made available in April 2025.

# Observations about gcu_rsds.xsd

The observations below are based on anecdotal evidence and would need systematic checking. They underpin the initial
choices made for the XSD to TTL transformation.

## xs:int vs. xs:integer

In some restrictions, we find both xs:int and xs:integer being used as a base type.

xs:integer is a primitive type in XSD. xs:int is a 32-bit signed integer, a pre-defined derived type of xs:integer.

For instance, the number of bogies is expressed as an xsd:int, while the wheelset gauge is an xs:integer.

It seems that the distinction is "legacy" (serving some old compatibility issues) and serves no semantic purpose. It can
be discarded in the course of the transformation.

## NumericX-Y types

These are decimal types with limited digits: at least X, at most Y.

The definition of these custom types is not provided in the XSD, neither as restrictions, nor in the documentation.

## Restriction ranges

Restriction ranges (xs:minInclusive, xs:maxInclusive) in general limit the number of decimal digits, rather than a
reasonable range of values. Examples:

| Parameter        | tolerated values (as per xs:restriction) |
|------------------|------------------------------------------|
| Wheel diameter   | 1 - 9999                                 |
| Wheelset gauge   | 1 - 9999                                 |
| Number of bogies | 1 - 9                                    |
| Bogie pitch      | 1 - 99999                                |

Considering the above:

* the restrictions should not become OWL restrictions, as they have no semantic value.
* it is not urgent to convert them to SHACL, as "max number of digits" is quite platform-specific.

Besides, tolerating wheel diameter values in less than 3 decimal digits does not seem advisable.

## Enumerations

Enumeration semantics is mostly encountered in annotations.

For instance: XSD element CouplingType has base type xs:token, and is restricted to 5 enumerated values ("0" to "4").
xs:token is a
kind of normalized string, with normalized usage of white space (no leading, no trailing, an internal collapsed into one
if any).

The annotation to element coupling type tell us what each enumeration value means:

| Enumeration value (string) | meaning                                   |
|----------------------------|-------------------------------------------|
| 0                          | without coupler                           |
| 1                          | non-reinforced coupler less than 85t      |
| 2                          | reinforced coupler equals to 85t          |
| 3                          | ultra-reinforced coupler greater than 85t |
| 4                          | automatic	coupling                        |

Beyond the syntactic transformation from XSD to RDF/OWL, we should replace each enumeration entry by a skos:concept,
annotated as follows:

* use the alphanumeric values as skos:prefLabel (for backward compatibility)
* use <coupling type concept scheme identifier>_<enum value> as skos:concept identifier
* use the meaning as skos:definition, for each skos:concept ( = enumeration entry).

Annotations should be done after the transformation, on a semi-automated bases (after capturing the annotations in a CSV
file).