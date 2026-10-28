# AEGIS WordPress verification

Zip the `aegis-verify` folder, install it through WordPress Plugins > Add New > Upload, and activate as an administrator. Open Settings > AEGIS verification. In AEGIS choose meta-tag verification, generate instructions, and copy the WordPress challenge JSON. Paste/save in WordPress, clear page caches, then check ownership in AEGIS.

The plugin publishes a short-lived public challenge in the homepage head. It accepts only the exact WordPress home origin and a challenge expiring within one hour. WordPress Settings API supplies the administrator capability and nonce checks. No remote commands, credentials, scanning or production edits are exposed. AEGIS consumes a successful challenge once and requires separate assessment consent.

Clear the challenge or deactivate to stop publishing it, purge caches, and revoke the asset in AEGIS to invalidate any already issued authorization immediately. Expiry does not purge third-party caches. Themes must call wp_head. A site served under a subdirectory must expose the token at the exact origin homepage or use DNS instead.

Implementation references: https://developer.wordpress.org/plugins/settings/using-settings-api/ and https://developer.wordpress.org/reference/hooks/wp_head/ . Local plugin-runtime and full WordPress acceptance results must be recorded separately; do not imply live installation.
