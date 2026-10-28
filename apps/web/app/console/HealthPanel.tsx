'use client';
import {useEffect,useState} from 'react';
type API=(p:string,m?:string,d?:unknown)=>Promise<any>;
export default function HealthPanel({api,org,assets,canManage=false}:{api:API;org:string;canManage?:boolean;assets:{id:string;origin:string;verified:boolean}[]}){
 const [rows,setRows]=useState<any[]>([]),[samples,setSamples]=useState<any[]>([]),[asset,setAsset]=useState(''),[path,setPath]=useState('/'),[interval,setInterval]=useState(900),[consent,setConsent]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 async function load(){setRows(await api(`/organizations/${org}/health-monitors`))}
 useEffect(()=>{let active=true;api(`/organizations/${org}/health-monitors`).then(r=>{if(active)setRows(r)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[api,org]);
 async function act(fn:()=>Promise<void>){setBusy(true);setError('');try{await fn()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <section className="glass panel"><h3>Website health monitoring</h3><p>Independent availability checks on one approved public endpoint. Each check revalidates ownership, consent and permissions. Monitoring ends when ownership or consent expires. Domain expiry is unavailable; no date is inferred.</p>
 {error&&<p role="alert">{error}</p>}{canManage&&<form className="form" onSubmit={e=>{e.preventDefault();act(async()=>{await api(`/assets/${asset}/health-monitor`,'PUT',{accepted:consent,path,interval_seconds:interval,hours:24});setConsent(false);await load()})}}>
 <label>Verified website<select value={asset} onChange={e=>{setAsset(e.target.value);setConsent(false)}}><option value="">Choose a website</option>{assets.filter(a=>a.verified).map(a=><option key={a.id} value={a.id}>{a.origin}</option>)}</select></label>
 <label>Approved health path<input value={path} onChange={e=>{setPath(e.target.value);setConsent(false)}}/></label>
 <label>Check interval<select value={interval} onChange={e=>{setInterval(Number(e.target.value));setConsent(false)}}><option value={300}>Every 5 minutes</option><option value={900}>Every 15 minutes</option><option value={3600}>Every hour</option><option value={86400}>Daily</option></select></label>
 <label className="check"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>I authorize one bounded GET per interval to this exact path for up to 24 hours. This does not authorize security assessments or edits.</label>
 <button disabled={busy||!asset||!consent}>Authorize health monitoring</button></form>}
 <button disabled={busy} onClick={()=>act(load)}>Refresh health status</button>
 {rows.map(r=><div className="row" key={r.id}><div className="grow"><strong>{r.origin}</strong><p>{r.last_status} · {r.enabled?'Enabled':'Disabled'} · consent ends {new Date(r.expires*1000).toLocaleString()}</p></div><button onClick={()=>act(async()=>setSamples(await api(`/health-monitors/${r.id}/samples`)))}>View history</button><a href={`/api/health-monitors/${encodeURIComponent(r.id)}/report.pdf`} download>Observations PDF</a>{canManage&&r.enabled&&<button onClick={()=>act(async()=>{await api(`/health-monitors/${r.id}`,'DELETE');await load()})}>Disable monitor</button>}</div>)}
 {samples.map(s=><div className="row" key={s.id}>{new Date(s.created*1000).toLocaleString()} · {s.status} · HTTP {s.http_status??'unavailable'} · {s.response_ms==null?'No timing':Math.round(s.response_ms)+' ms'} · TLS expiry {s.tls_expires?new Date(s.tls_expires*1000).toLocaleString():'unavailable'}</div>)}
 </section>
}
