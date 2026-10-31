import {firebaseHelperProxy} from '../../../../lib/firebase-helper-proxy';
export const runtime='nodejs';
export const dynamic='force-dynamic';
type Context={params:Promise<{path:string[]}>};
async function handle(request:Request,context:Context){
 const segments=(await context.params).path;
 if(!segments||segments.length!==1)return new Response('Not found.',{status:404});
 return firebaseHelperProxy(request,'/__/auth/'+segments[0]);
}
export const GET=handle;
export const HEAD=handle;
export const POST=handle;
