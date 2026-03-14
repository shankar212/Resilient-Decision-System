from typing import Dict, Any, Tuple, Optional, List

def evaluate_rule(rule: Dict[str, Any], payload: Dict[str, Any]) -> bool:
    """
    Evaluates a single rule against a payload.
    Returns True if the rule passes, False otherwise.
    """
    rule_type = rule.get("type")
    field = rule.get("field")
    
    # Optional field check handling can be expanded, but usually mandatory checks handle presence
    actual_value = payload.get(field)

    if rule_type == "mandatory":
        return actual_value is not None and str(actual_value).strip() != ""
        
    elif rule_type == "equality":
        target_value = rule.get("value")
        return actual_value == target_value
        
    elif rule_type == "threshold":
        op = rule.get("operator")
        target_value = rule.get("value")
        
        if actual_value is None:
            return False
            
        try:
            # Try numeric comparison if possible
            actual_num = float(actual_value)
            target_num = float(target_value)
            
            if op == ">": return actual_num > target_num
            elif op == ">=": return actual_num >= target_num
            elif op == "<": return actual_num < target_num
            elif op == "<=": return actual_num <= target_num
            elif op == "==": return actual_num == target_num
            elif op == "!=": return actual_num != target_num
        except (ValueError, TypeError):
            # Fallback to string comparison or just fail
            pass
            
    return False

def evaluate_stage_rules(rules: List[Dict[str, Any]], payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Evaluates all rules in a stage.
    Returns (True, None) if all rules pass.
    Returns (False, failed_rule) if any rule fails.
    """
    for rule in rules:
        if not evaluate_rule(rule, payload):
            return False, rule
    return True, None
