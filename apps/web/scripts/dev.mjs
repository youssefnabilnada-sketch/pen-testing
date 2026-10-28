// Normalize dev-server CLI flags for Next.js and the managed preview supervisor.
import {spawn} from 'node:child_process';
const args=process.argv.slice(2);
const value=(key,fallback)=>args.includes(key)?args[args.indexOf(key)+1]:fallback;
const child=spawn(process.execPath,['node_modules/next/dist/bin/next','dev','--hostname',value('--host','0.0.0.0'),'--port',value('--port',process.env.PORT||'3000')],{stdio:'inherit'});
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>child.kill(signal));
child.on('exit',code=>process.exit(code??1));
