# About the output files

There are some minor quirks remaining.

One of them is commercialTrafficType, defined as an object property and a data property at the same time: not corrected for the time being, as the source XSD looks suspicious:

```xml
	<xs:element name="PlannedTrainData">
		<xs:annotation>
			<xs:documentation>Train relevant data for a planning period</xs:documentation>
		</xs:annotation>
		<xs:complexType>
			<xs:sequence>
				<xs:element ref="TrainType" minOccurs="0"/>
				<xs:element ref="TrafficType" minOccurs="0"/>
				<xs:element ref="PushPullTrain" minOccurs="0"/>
				<xs:element ref="TypeofService" minOccurs="0"/>
				<xs:element name="CommercialTrafficType" type="tap:type7009BrandNameCodeList" minOccurs="0"/>
				<xs:element ref="PlannedTrainTechnicalData"/>
				<xs:element ref="ExceptionalGaugingIdent" minOccurs="0" maxOccurs="unbounded"/>
				<xs:element ref="DangerousGoodsIndication" minOccurs="0" maxOccurs="unbounded"/>
				<xs:element ref="CombinedTrafficLoadProfile" minOccurs="0"/>
			</xs:sequence>
		</xs:complexType>
	</xs:element>
```
Type `tap:type7009BrandNameCodeList` is not defined in the source XSDs. On the other hand, the other entries in the sequence are properly handled as object properties.
