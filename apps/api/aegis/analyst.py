"""Provider boundary. Current build intentionally uses deterministic explanations only.
No page bodies or arbitrary scanner strings become instructions. No tool execution.
"""
from typing import Protocol
import re
from .checks import RULES as BASE_RULES
from .api_assessment import RULES as API_RULES
from .detectors import CATALOG
RULES={**BASE_RULES, **API_RULES, "header.referrer":("Referrer Policy not observed","low","Review and set an explicit Referrer-Policy appropriate to application privacy needs.")}

RULES.update({key:(rule['title'],'low',rule['fix']) for key,rule in CATALOG.items()})

class ExplanationProvider(Protocol):
    def explain(self, rule_ids: list[str]) -> dict: ...

class RuleBasedAnalyst:
    def explain(self, rule_ids):
        known = [r for r in rule_ids if r in RULES or (re.fullmatch(r'[^@]+@[a-f0-9]{16}',r) and r.split('@')[0] in RULES)]
        return {
            'mode':'rule-based fallback',
            'summary':f'{len(known)} configuration observations require review.' if known else 'No supported configuration findings were recorded. This does not establish that the website is secure.',
            'limitations':'Explicitly authorized response paths only. No authenticated paths, application logic testing, exploitation or comprehensive penetration testing.',
            'business_impact':'Configuration gaps can weaken browser-side defenses. Actual business impact and exploitability depend on the application and require human review.',
            'recommendations':[{'rule':r,'action':RULES[r.split('@')[0]][2],'classification':'recommendation, not a verified vulnerability'} for r in known]
        }
