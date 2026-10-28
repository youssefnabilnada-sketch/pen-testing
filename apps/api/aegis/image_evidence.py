"""Decode and re-encode bounded PNG evidence without metadata or animation."""
import base64
from io import BytesIO
from PIL import Image

def sanitize_png(content):
    raw=base64.b64decode(content,validate=True)
    if len(raw)>262144:raise ValueError('Image exceeds 256 KiB.')
    with Image.open(BytesIO(raw)) as im:
        if im.format!='PNG' or getattr(im,'n_frames',1)!=1:raise ValueError('Single-frame PNG required.')
        if im.width*im.height>4_000_000:raise ValueError('Image exceeds four megapixels.')
        im.load()
        clean=Image.new('RGBA',im.size);clean.paste(im.convert('RGBA'));out=BytesIO();clean.save(out,format='PNG')
    data=out.getvalue()
    if len(data)>262144:raise ValueError('Normalized image exceeds 256 KiB.')
    return base64.b64encode(data).decode('ascii'),len(data)
