# Define XML Schema namespace constant
XS_NS = "{http://www.w3.org/2001/XMLSchema}"


def is_functional(element):
    """Check if an element should be a functional property."""
    max_occurs = element.get('maxOccurs')
    min_occurs = element.get('minOccurs')

    if max_occurs == '1':
        return True
    elif min_occurs is None and max_occurs is None:
        return True
    return False


def get_documentation(element):
    """Extract documentation from an element if available."""
    for child in element:
        if child.tag == f"{XS_NS}annotation":
            for doc in child:
                if doc.tag == f"{XS_NS}documentation":
                    return doc.text.strip() if doc.text else None
    return None
