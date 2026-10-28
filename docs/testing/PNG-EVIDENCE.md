# PNG evidence implementation status

Added bounded single-frame PNG upload using base64 JSON and Pillow decoding/re-encoding.
Input/output are capped at 256 KiB; decoded dimensions capped at four megapixels. Metadata
is stripped. Existing tenant/private attachment checks and forced binary download remain.
No schema migration: .png content is normalized base64 in the existing text column; earlier
text uploads could not use .png. New uploads explicitly choose text or base64 encoding.

Executed focused tests: test_image_evidence.py and test_attachments.py, 8 passed in 2.67s.
Metadata stripping and non-image rejection tested; existing attachment permission tests pass.
New PNG route end-to-end/browser tests, complete regression, dependency audit and production
memory/concurrency validation remain outstanding. Do not mark this feature complete yet.
No malware-scanner claim, PDF/JPEG upload or cloud storage implementation.

Follow-up executed verification:
- PNG API upload/download, nosniff attachment response, cross-tenant access rejection,
  text/binary mode confusion, fake-image rejection and pixel cap: focused suite 10 passes.
- Frontend tests: 50 passes, including explicit PNG encoding and protected download link.
- Complete backend suite: 194 passes, 1 skip, 71.98s; png-full.xml/log.
- Next production build passed: png-build.log. OpenAPI regenerated.
- `pip_audit -r apps/api/requirements.txt --disable-pip --no-deps`: no known vulnerabilities
  found for direct listed requirements. Transitive dependency audit is not covered by this command.
- Ruff configured checks and whitespace check passed.

This supersedes the earlier outstanding API/component/full-regression items. Browser visual
acceptance, production memory/concurrency testing and whole-product completion remain unverified.
