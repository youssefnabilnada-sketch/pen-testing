# PHP inventory matching

Added conservative CPE php:php stable numeric version boundaries through the existing
inventory matcher. Inclusive/exclusive boundaries and exact stable versions are supported;
vendor-suffixed builds, release candidates, unknown constraints and unbounded product-only
records remain unknown. Existing advisory ingestion, provenance and notifications are used.
This is declared-inventory matching, not intrusive PHP fingerprinting or runtime exploitation.
NVD environment conditions/backported patches still require review. It does not prove a
website vulnerable or fixed, and does not add an advisory-specific assessment detector.

Executed: pytest tests/test_php_inventory.py tests/test_intelligence.py -q
Result: 30 passed, 7.84s; php-inventory.xml/log. Ruff configured checks and diff check passed.
Fixtures are synthetic range tests, not claims that live PHP advisories were synchronized.
No live feed, public scan, deployment or new complete-suite coverage claim.
