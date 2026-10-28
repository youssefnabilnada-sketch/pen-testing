from types import SimpleNamespace
import pytest
from aegis.intelligence.service import version_match

@pytest.mark.parametrize('version,expected',[('8.3.1',True),('8.3.35',True),('8.3.36',False),('8.4.0',False),('8.3.35-vendor1',None),('8.3.36RC1',None),('',None)])
def test_php_stable_bounds(version,expected):
    advisory={'name':'php:php','version':'*','constraints':{'versionStartIncluding':'8.3.0','versionEndExcluding':'8.3.36'}}
    assert version_match(SimpleNamespace(ecosystem='cpe',version=version),advisory) is expected

@pytest.mark.parametrize('constraints',[{'unknown':'8.3.0'},{'versionEndExcluding':'8.3.36RC1'},{}])
def test_unsupported_evidence_stays_unknown(constraints):
    assert version_match(SimpleNamespace(ecosystem='cpe',version='8.3.35'),{'name':'php:php','version':'*','constraints':constraints}) is None
