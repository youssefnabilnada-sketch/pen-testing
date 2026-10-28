# Optional GitHub integration

Keep GITHUB_ENABLED=false until an operator configures a GitHub App. Select only authorized repositories; grant contents read/write, pull requests read/write and checks read. Enable user authorization and configure the callback to the deployed HTTPS frontend /console URL. Configure GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI and a separately generated Fernet GITHUB_TOKEN_KEY on the API only. Never add private values to Git or frontend environment variables.

Apply migration 010_github. From Remediation, authorize the connection, return from GitHub, complete the connection for the originating workspace, select a repository and an accepted remediation request. Only an existing vercel.json and the supported missing nosniff observation have an automated proposal. Other findings require engineer-managed remediation. Enable authenticator MFA in Account before publishing a reviewed draft PR.

No automatic merge or deployment is performed. Application CI and staging validation remain necessary. After approved deployment, record evidence and rollback information in the remediation request, then authorize full retesting. A PR merge never marks a website fixed.

Expired tokens require reconnection. An uncertain publication is not retried automatically: inspect the dedicated aegis/review-* branch and PR in GitHub. POST /admin/repository-control with {"accepted":true} pauses new publications; false resumes them. Existing remote operations cannot be undone by this flag.

Live GitHub connectivity has not been verified in this execution environment. Provider fixtures verify payloads, access controls and lifecycle behavior; they do not demonstrate a real installation.
