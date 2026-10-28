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
