<?php
// Run only against an isolated WordPress installation. No email or external network.
define('WP_INSTALLING', true);
function wp_mail($to,$subject,$message,$headers='',$attachments=array()){return true;}
require getenv('AEGIS_WORDPRESS_ROOT').'/wp-load.php';
require_once ABSPATH.'wp-admin/includes/upgrade.php';
require_once ABSPATH.'wp-admin/includes/plugin.php';
function check_aegis($condition,$label){if(!$condition)throw new Exception($label);echo $label." passed\n";}
if(!is_blog_installed())wp_install('AEGIS fixture','aegis_admin','admin@example.test',false,'',bin2hex(random_bytes(20)));
$admin=get_user_by('login','aegis_admin');wp_set_current_user($admin->ID);
$result=activate_plugin('aegis-verify/aegis-verify.php');check_aegis(!is_wp_error($result),'Actual plugin activation');
do_action('admin_init');
$challenge=array('origin'=>'https://owned.example','token'=>str_repeat('x',43),'expires'=>time()+1800);
update_option('aegis_verify_challenge',json_encode($challenge));
check_aegis(get_option('aegis_verify_challenge')['token']===$challenge['token'],'WordPress Settings API storage');
$GLOBALS['wp_query']=new WP_Query();$GLOBALS['wp_query']->is_home=true;
ob_start();do_action('wp_head');$html=ob_get_clean();
check_aegis(str_contains($html,'name="aegis-verification" content="'.$challenge['token'].'"'),'WordPress frontend hook publication');
$subscriber=get_user_by('login','aegis_subscriber');
if(!$subscriber){$uid=wp_create_user('aegis_subscriber',bin2hex(random_bytes(20)),'subscriber@example.test');$subscriber=get_user_by('id',$uid);}
$subscriber->set_role('subscriber');wp_set_current_user($subscriber->ID);
update_option('aegis_verify_challenge','');
check_aegis(get_option('aegis_verify_challenge')['token']===$challenge['token'],'Subscriber cannot disconnect proof');
wp_set_current_user($admin->ID);
$bad=$challenge;$bad['origin']='https://foreign.example';update_option('aegis_verify_challenge',json_encode($bad));
check_aegis(get_option('aegis_verify_challenge')['origin']==='https://owned.example','Foreign origin rejected');
$bad=$challenge;$bad['expires']=time()-1;update_option('aegis_verify_challenge',json_encode($bad));
check_aegis(get_option('aegis_verify_challenge')['expires']===$challenge['expires'],'Expired proof rejected');
check_aegis(wp_verify_nonce(wp_create_nonce('aegis_verify-options'),'aegis_verify-options')!==false && wp_verify_nonce('invalid','aegis_verify-options')===false,'WordPress nonce validation');
deactivate_plugins('aegis-verify/aegis-verify.php');
check_aegis(get_option('aegis_verify_challenge',null)===null,'Deactivation removes stored proof');
echo 'WordPress '.$GLOBALS['wp_version'].' runtime acceptance completed.';
