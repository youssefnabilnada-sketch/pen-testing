# SmartVerify localized narrated video tutorials

## Verified release-candidate assets
- Fourteen verification topics, each with an **Arabic-only** and **English-only** original explainer MP4: 28 MP4 files in `apps/web/public/guides/videos/`.
- Every MP4 includes an **audio track** with spoken instructions in the matching language and a video track. One WebVTT caption file accompanies each MP4, so there are also 28 `.vtt` files.
- Arabic uses `<topic>-ar.mp4` and `<topic>-ar.vtt`; English uses `<topic>-en.mp4` and `<topic>-en.vtt`. Previous mixed-language `<topic>.mp4` assets were removed.
- Narration is synthetic; the producer favors an Arabic-Egyptian and English-American neural voice, with an offline language-specific fallback if the voice service fails. No customer data, credentials, real DNS tokens, or provider dashboard screenshots are included.
- Audio duration determines each slide's display time, so voice is not cut off. All tracks were checked using ffprobe during generation.

## Customer experience
- `/guides` is public and does not require an AEGIS account.
- The language setting stored by `Experience` determines which localized video and caption track the gallery serves. Changing language remounts the player and selects the proper clip without showing the other language in that video.
- SmartVerify's ownership wizard uses the same language selection and preserves all server-side ownership/assessment protections.
- A download link uses the matching localized MP4 name. Interactive text walkthroughs remain a separate option.

## Reproduction / acceptance
- Source generator: `scripts/render_ownership_videos.py`.
- CI generator: `.github/workflows/build-aegis-tutorial-videos.yml`.
- Browser checks: `apps/web/e2e/public-guides.spec.ts` verifies locale changes and all 28 media/caption routes on desktop and mobile.
- Frontend checks: `apps/web/tests/public-guides.test.tsx` verifies language-switching without calls to customer/account APIs.
- Do not release the current UI into Production until the latest exact-SHA CI and preview are green and the separately tracked Oracle/customer live sign-in, consent and scan acceptance gates are approved.

These videos are illustrative guides, not recordings of real provider accounts or promises of direct Google/hosting OAuth verification.
