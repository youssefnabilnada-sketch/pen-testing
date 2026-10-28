# Optional Cloudflare SmartVerify TXT helper

**Status:** source implementation and offline tests available; not live-provider certified or permission to scan.

The helper creates **one** short-lived AEGIS ownership TXT proof, never deletes/updates existing records, never lists arbitrary DNS zones, and never starts a website assessment. The user must already control a registered AEGIS asset, have a current DNS challenge, belong to the asset's workspace as an owner/admin, be email-verified, and explicitly confirm the proposed change. Existing MFA, when configured, is required for publication.

In the Ownership guide select **DNS** and create the challenge. Expand the Cloudflare helper and choose **Review exact DNS change**. Review the record, supply the Cloudflare **Zone ID** and a short-lived API Token restricted to that zone with `Zone → Zone → Read` and `Zone → DNS → Edit` (Cloudflare DNS Write). Check the confirmation box and publish the single TXT record. After DNS propagation, press **Check ownership** separately. Don't grant global Cloudflare keys or share them in chats, files or source control. Revoke the limited token at Cloudflare after use.

The backend sends HTTPS requests only to `https://api.cloudflare.com/client/v4`, with no environment proxies or redirects and a bounded timeout. It verifies the zone name matches the registered hostname, lists the existing challenge TXT records, prevents duplicate publication of identical proof, validates the live challenge and workspace permission again before the write, and creates only the derived TXT record. Cloudflare tokens are used ephemerally, represented as Pydantic `SecretStr`, never persisted to DB or returned in API responses. It logs only action identifiers. API failures are generic and do not expose credential details. Note that HTTP access logs, reverse proxies and browser instrumentation must also avoid logging request bodies in production.

API endpoints: 

- `GET /assets/{asset_id}/challenge/{challenge_id}/cloudflare/preview` — logged-in owner/admin preview, no provider call.
- `POST /assets/{asset_id}/challenge/{challenge_id}/cloudflare/publish` — `zone_id`, `api_token`, `confirm_dns_change: true`, optional `mfa_code` if the customer account uses MFA. API token is accepted only in JSON body, not URL query.

This does **not** automatically prove domain ownership. AEGIS still must verify the published TXT through its independent DNS verification route; that verification does **not** grant permissions for scanning, staging, code changes or AutoFix. The helper makes no direct modifications to WordPress, Vercel, Netlify, cPanel, Plesk or GitHub projects.

## Tests and rollout

- Offline provider tests: `PYTHONPATH=apps/api python -m unittest discover -s tests -p 'test_cloudflare_provider_unit.py' -v`.
- API authorization tests: `PYTHONPATH=apps/api python -m pytest tests/test_cloudflare_smartverify_api.py -q` in fully provisioned CI, with dependencies installed.
- UI tests: `cd apps/web && npm ci && npm test` (includes `ownership-cloudflare.test.tsx`).
- Before accepting live requests, run a controlled integration test against a dedicated *owned* Cloudflare test zone with a least-privilege disposable token and verify real DNS propagation, expiry and cleanup manually. **No live zone was used in this development environment.**

Sources: https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/create/ and https://developers.cloudflare.com/api/resources/zones/methods/list/.
