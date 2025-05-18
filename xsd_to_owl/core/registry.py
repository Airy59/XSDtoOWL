# xsd_to_owl/core/registry.py
class RuleRegistry:
    """
    Registry for transformation rules.
    Stores and manages access to transformation rules.
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._rules = []
        self._active_rules = set()

    def register_rule(self, rule):
        """
        Register a transformation rule.

        Args:
            rule: An XSDVisitor implementation

        Returns:
            The registry instance for chaining
        """
        self._rules.append(rule)
        self._active_rules.add(rule.rule_id)
        return self

    def get_rules(self):
        """
        Get all registered rules.

        Returns:
            List of registered rules
        """
        return list(self._rules)

    def get_active_rules(self):
        """
        Get only active rules.

        Returns:
            List of active rules
        """
        return [rule for rule in self._rules if rule.rule_id in self._active_rules]

    def activate_rule(self, rule_id):
        """
        Activate a rule by ID.

        Args:
            rule_id: ID of the rule to activate
        """
        self._active_rules.add(rule_id)

    def deactivate_rule(self, rule_id):
        """
        Deactivate a rule by ID.

        Args:
            rule_id: ID of the rule to deactivate
        """
        if rule_id in self._active_rules:
            self._active_rules.remove(rule_id)

    def get_rule_by_id(self, rule_id):
        """
        Get a rule by its ID.

        Args:
            rule_id: ID of the rule to retrieve

        Returns:
            The rule or None if not found
        """
        for rule in self._rules:
            if rule.rule_id == rule_id:
                return rule
        return None