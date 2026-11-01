# AEGIS public verification video-only release

Built from release/aegis-v1-final, independent of PR #21.
This change adds a bilingual public video gallery at /guides, embeds native narrated MP4 tutorials within the *existing* ownership verification wizard, and links the gallery from the landing and account pages.

Media: 28 narrated MP4s (14 separate Arabic and English topic pairs), 28 WebVTT caption tracks. Reuses exact candidate Git blobs without regenerating or compressing existing audio. Guides are illustrative animations rather than recordings of provider dashboards.

UNCHANGED: auth routes, Firebase/Brevo, Caddy/Oracle/Docker, scanner, tenant isolation, backend, database migrations, payment configuration, site ownership verification implementation, authorization policy, secrets, public registration flags.

Check desktop and mobile: select provider and proof method, verify that the displayed MP4 and captions match the UI language, confirm that /guides works without AEGIS login, and ensure using videos never generates a proof token or starts an assessment. The existing protected customer sign-in and launch-readiness gates remain separate; deploying tutorials does not imply the whole AEGIS service is open for new customers.
