<?php
/**
 * Plugin Name: AEGIS Ownership Verification
 * Description: Publishes an expiring ownership challenge. No scanning, account credentials or remote editing.
 * Version: 1.0.0
 * Requires PHP: 8.0
 */
if (!defined('ABSPATH')) { exit; }
function aegis_verify_validate($value) {
    if (!current_user_can('manage_options')) { return get_option('aegis_verify_challenge', array()); }
    if ($value === '') { return array(); }
    $data = is_string($value) ? json_decode($value, true) : $value;
    $home = wp_parse_url(home_url('/'));
    $origin = strtolower($home['scheme'] . '://' . $home['host']);
    if (isset($home['port'])) { $origin .= ':' . $home['port']; }
    if (!is_array($data) || !isset($data['token'], $data['expires'], $data['origin']) ||
        !is_string($data['token']) || !preg_match('/^[A-Za-z0-9_-]{20,100}$/D', $data['token']) ||
        !is_numeric($data['expires']) || $data['expires'] <= time() || $data['expires'] > time()+3600 ||
        !is_string($data['origin']) || $data['origin'] !== $origin) {
        add_settings_error('aegis_verify_challenge','invalid','Use an unexpired AEGIS WordPress challenge for this exact website.');
        return get_option('aegis_verify_challenge', array());
    }
    return array('token'=>$data['token'],'expires'=>(int)$data['expires'],'origin'=>$origin);
}
add_action('admin_init', function() {
    register_setting('aegis_verify', 'aegis_verify_challenge', array('sanitize_callback'=>'aegis_verify_validate','default'=>array(),'show_in_rest'=>false));
});
add_action('admin_menu', function() {
    add_options_page('AEGIS verification','AEGIS verification','manage_options','aegis-verify','aegis_verify_page');
});
function aegis_verify_page() {
    if (!current_user_can('manage_options')) { wp_die('Administrator permission required.'); }
    echo '<div class="wrap"><h1>AEGIS ownership verification</h1><p>Paste the WordPress challenge from your AEGIS ownership guide. This only publishes a temporary proof; it grants no scan or editing permission.</p>';
    settings_errors('aegis_verify_challenge');
    echo '<form action="options.php" method="post">';
    settings_fields('aegis_verify');
    $data=get_option('aegis_verify_challenge', array());
    echo '<label for="aegis-challenge">Challenge JSON (clear to disconnect)</label><br><textarea id="aegis-challenge" name="aegis_verify_challenge" rows="6" cols="80">';
    echo esc_textarea($data ? wp_json_encode($data) : '');
    echo '</textarea><p>After saving, clear your page cache and return to AEGIS to check ownership. To revoke previously verified access, also choose Revoke in AEGIS. Cached pages must be purged when disconnecting.</p>';
    submit_button('Save challenge');
    echo '</form></div>';
}
add_action('wp_head', function() {
    $data=get_option('aegis_verify_challenge', array());
    if (is_front_page() && is_array($data) && isset($data['token'],$data['expires']) && $data['expires']>time()) {
        echo '<meta name="aegis-verification" content="'.esc_attr($data['token']).'">'."\n";
    }
});
register_deactivation_hook(__FILE__, function() { delete_option('aegis_verify_challenge'); });
