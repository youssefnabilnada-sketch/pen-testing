import base64
from io import BytesIO
import pytest
from PIL import Image,PngImagePlugin
from aegis.image_evidence import sanitize_png

def test_reencodes_and_removes_metadata():
    out=BytesIO();meta=PngImagePlugin.PngInfo();meta.add_text('secret','private-value')
    Image.new('RGB',(4,4)).save(out,format='PNG',pnginfo=meta)
    value,size=sanitize_png(base64.b64encode(out.getvalue()).decode())
    raw=base64.b64decode(value);assert size==len(raw) and b'private-value' not in raw
    assert Image.open(BytesIO(raw)).size==(4,4)

@pytest.mark.parametrize('value',['notbase64','PHN2Zz48L3N2Zz4=',''])
def test_rejects_non_images(value):
    with pytest.raises(Exception):sanitize_png(value)

def test_png_api_roundtrip_and_tenant_isolation(client,mail):
    from conftest import signup
    from test_attachments import create
    from fastapi.testclient import TestClient
    from aegis.main import app
    org=signup(client,mail);ticket=create(client,org);path=f'/files/support/{ticket}'
    image=BytesIO();Image.new('RGB',(3,3)).save(image,format='PNG')
    payload={'filename':'screen.png','encoding':'base64','content':base64.b64encode(image.getvalue()).decode()}
    result=client.post(path,json=payload);assert result.status_code==201
    aid=result.json()['id'];download=client.get(path+'/'+aid)
    assert Image.open(BytesIO(download.content)).size==(3,3)
    assert download.headers['content-type']=='application/octet-stream'
    assert download.headers['x-content-type-options']=='nosniff'
    outsider=TestClient(app);signup(outsider,mail,'image-other@example.test')
    assert outsider.get(path+'/'+aid).status_code==403
    assert outsider.post(path,json=payload).status_code==403
    assert client.post(path,json={**payload,'encoding':'text'}).status_code==422
    assert client.post(path,json={**payload,'content':'PHN2Zz48L3N2Zz4='}).status_code==422

def test_png_pixel_limit():
    image=BytesIO();Image.new('L',(2001,2000)).save(image,format='PNG')
    with pytest.raises(ValueError):sanitize_png(base64.b64encode(image.getvalue()).decode())
