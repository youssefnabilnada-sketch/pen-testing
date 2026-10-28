<?php
// PHP execution with a minimal WordPress contract double, not a full WordPress installation.
define('ABSPATH',__DIR__);
$GLOBALS['allowed']=true;$GLOBALS['options']=array();$GLOBALS['hooks']=array();$GLOBALS['errors']=array();
function current_user_can($cap){return $GLOBALS['allowed'] && $cap==='manage_options';}
function get_option($key,$fallback=null){return $GLOBALS['options'][$key]??$fallback;}
function delete_option($key){unset($GLOBALS['options'][$key]);}
function wp_parse_url($url){return parse_url($url);}
function home_url($path){return 'https://owned.example/';}
function add_settings_error($key,$code,$message){$GLOBALS['errors'][]=$code;}
function add_action($hook,$fn){$GLOBALS['hooks'][$hook]=$fn;}
function register_deactivation_hook($file,$fn){$GLOBALS['deactivate']=$fn;}
function is_front_page(){return true;}
function esc_attr($text){return htmlspecialchars($text,ENT_QUOTES);}
function expect_true($value,$message){if(!$value){throw new Exception($message);}}
require __DIR__.'/../integrations/wordpress/aegis-verify/aegis-verify.php';
$good=array('origin'=>'https://owned.example','token'=>str_repeat('a',43),'expires'=>time()+1800);
$valid=aegis_verify_validate(json_encode($good));
expect_true($valid['token']===$good['token'],'Valid challenge rejected');
$GLOBALS['options']['aegis_verify_challenge']=$valid;
foreach (array(array('origin'=>'https://foreign.example'),array('expires'=>time()-1),array('expires'=>time()+7200),array('token'=>'"><script>bad</script>')) as $change) {
 $before=count($GLOBALS['errors']);aegis_verify_validate(json_encode(array_merge($good,$change)));
 expect_true(count($GLOBALS['errors'])===$before+1,'Unsafe challenge accepted');
}
$GLOBALS['allowed']=false;
expect_true(aegis_verify_validate('')===$valid,'Nonadministrator cleared challenge');
$GLOBALS['allowed']=true;
ob_start();$GLOBALS['hooks']['wp_head']();$output=ob_get_clean();
expect_true(str_contains($output,'name="aegis-verification"'),'Challenge not published');
$GLOBALS['options']['aegis_verify_challenge']['expires']=time()-1;
ob_start();$GLOBALS['hooks']['wp_head']();$output=ob_get_clean();
expect_true($output==='','Expired challenge published');
expect_true(aegis_verify_validate('')===array(),'Disconnect rejected');
$GLOBALS['deactivate']();
expect_true(get_option('aegis_verify_challenge')===null,'Deactivation retained challenge');
echo "WordPress contract execution: valid token, origin, expiry, injection, permissions, publication and disconnect passed\n";
