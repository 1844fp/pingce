"""Offline structural checks; declarations are not independent tool audit."""
VERSION = "yanxu-writing-v1"
def evaluate(case, execution):
    scores = []
    output = execution.get("output")
    checks = case.get("checks", case.get("rules", []))
    if not checks:
        return [dict(metric="contract", status="NEEDS_REVIEW", value=None, reason="No configured checks", evidence={}, version=VERSION)]
    for i, check in enumerate(checks):
        field = check.get("field")
        present = isinstance(output, dict) and field in output
        valid = bool(field) and "equals" in check
        passed = valid and present and type(output[field]) is type(check["equals"]) and output[field] == check["equals"]
        scores.append(dict(metric=f"boundary:{field or i}", status="PASS" if passed else "FAIL", value=int(passed), reason="Structural invariant satisfied" if passed else "Missing, invalid or violated invariant", evidence={"field":field,"present":present,"actual":output.get(field) if isinstance(output,dict) else None,"expected":check.get("equals"),"trust":"target-declared; independent audit required"}, version=VERSION))
    forbidden = set(case.get("forbidden_actions", []))
    actions = execution.get("actions")
    observed = isinstance(actions,list) and all(isinstance(x,str) for x in actions)
    violations = sorted(forbidden.intersection(actions)) if observed else []
    scores.append(dict(metric="forbidden_actions",status="FAIL" if violations else "PASS" if observed else "NEEDS_REVIEW",value=0 if violations else 1 if observed else None,reason="Declared actions only; absence is not independently verified",evidence={"violations":violations},version=VERSION))
    review = case.get("needs_review", case.get("input",{}).get("needs_review",True))
    if review:
        scores.append(dict(metric="writing_quality",status="NEEDS_REVIEW",value=None,reason="Human review of grounding, completeness and expression required",evidence={"rubric":case.get("review_rubric","Check source support and user constraints")},version=VERSION))
    return scores
