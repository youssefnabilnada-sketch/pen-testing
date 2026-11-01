import pytest
from aegis.repositories import propose_nosniff

@pytest.mark.parametrize('source',[
    '{"version":1,"version":2}',
    '{"unknown":NaN}',
    '{"unknown":Infinity}',
    '{"unknown":-Infinity}',
    '{"description":"'+'é'*33000+'"}',
],ids=['duplicate-key','nan','infinity','negative-infinity','utf8-byte-budget'])
def test_ambiguous_or_invalid_source_requires_manual_review(source):
    with pytest.raises(ValueError):propose_nosniff(source)

@pytest.mark.parametrize('source',[
    '{"unknown":1e999}',
    '{"unknown":-1e999}',
    '{"unknown":1e-999}',
    '{"unknown":0.123456789012345678901}',
],ids=['exponent-overflow','negative-exponent-overflow','exponent-underflow','decimal-precision-loss'])
def test_numeric_values_that_cannot_roundtrip_require_manual_review(source):
    with pytest.raises(ValueError):propose_nosniff(source)


def test_proposal_output_must_remain_within_byte_budget():
    # The original is under 64 KiB but the appended security-header rule is not.
    original='{"description":"'+('x'*65480)+'"}'
    assert len(original.encode('utf-8'))<=65536
    with pytest.raises(ValueError,match='safe size'):propose_nosniff(original)


def test_supported_exact_numeric_value_still_preserves_existing_configuration():
    import json
    original='{"version":2,"threshold":1.25}'
    fixed=json.loads(propose_nosniff(original))
    assert fixed['version']==2 and fixed['threshold']==1.25
    assert fixed['headers'][-1]['headers'][0]['value']=='nosniff'


@pytest.mark.parametrize('source',['', ' ', '\n'])
def test_empty_or_whitespace_only_configuration_needs_manual_review(source):
    # An existing zero-length vercel.json is invalid JSON, not an empty object.
    with pytest.raises(ValueError):propose_nosniff(source)
