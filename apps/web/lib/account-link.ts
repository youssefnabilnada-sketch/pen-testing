export function accountLink(hash:string):{mode:'verify'|'reset';token:string}|null {
 const params=new URLSearchParams(hash.startsWith('#')?hash.slice(1):hash);
 const keys=Array.from(params.keys());
 if(keys.length!==1||!['verify','reset'].includes(keys[0]))return null;
 const token=params.get(keys[0])||'';
 if(!/^[A-Za-z0-9_-]{20,150}$/.test(token))return null;
 return {mode:keys[0] as 'verify'|'reset',token};
}
