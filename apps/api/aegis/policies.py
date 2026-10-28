"""Limited CSP directive extraction, not a browser policy evaluator."""
def csp_directives(value):
    directives={}
    for part in value.split(';'):
        tokens=part.strip().split()
        if tokens:directives.setdefault(tokens[0].lower(),[t.lower() for t in tokens[1:]])
    return directives

def single_csp(headers):
    policies=[v for k,v in headers if k.lower()=='content-security-policy']
    # Multiple policies require intersection semantics beyond this limited detector.
    return policies[0] if len(policies)==1 and ',' not in policies[0] else None
