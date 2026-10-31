import {firebaseHelperProxy} from '../../../lib/firebase-helper-proxy';
export const runtime='nodejs';
export const dynamic='force-dynamic';
export async function GET(request:Request){return firebaseHelperProxy(request,'/__/firebase/init.json');}
export async function HEAD(request:Request){return firebaseHelperProxy(request,'/__/firebase/init.json');}
