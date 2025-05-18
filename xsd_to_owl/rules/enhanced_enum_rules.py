# xsd_to_owl/rules/enhanced_enum_rules.py
"""
Enhanced enumeration rules with higher priority to ensure they run before DetectSimpleTypeRule.
"""
from xsd_to_owl.rules.enum_rules import EnhancedNamedEnumTypeRule, EnhancedAnonymousEnumTypeRule


class HighPriorityEnhancedNamedEnumTypeRule(EnhancedNamedEnumTypeRule):
    """Enhanced version of NamedEnumTypeRule with higher priority"""
    
    @property
    def priority(self):
        """Higher priority than DetectSimpleTypeRule to ensure this runs first"""
        return 350
    
    @property
    def rule_id(self):
        """Unique identifier for this rule"""
        return "high_priority_named_enum_type"


class HighPriorityEnhancedAnonymousEnumTypeRule(EnhancedAnonymousEnumTypeRule):
    """Enhanced version of AnonymousEnumTypeRule with higher priority"""
    
    @property
    def priority(self):
        """Higher priority than DetectSimpleTypeRule to ensure this runs first"""
        return 350
    
    @property
    def rule_id(self):
        """Unique identifier for this rule"""
        return "high_priority_anonymous_enum_type"