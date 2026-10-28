'use client';
import {useState} from 'react';
type API=(path:string,method?:string,data?:unknown)=>Promise<any>;
type Row={path:string;depth:number;source:string;status:string};
export default function RecursiveDiscovery({assetId,verified,api,onSelect}:{assetId:string;verified:boolean;api:API;onSelect:(paths:string[])=>void}){
 const [consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [paths,setPaths]=useState<string[]|null>(null),[chosen,setChosen]=useState<string[]>([]);
 const [budget,setBudget]=useState(10),[depth,setDepth]=useState(3),[prefixes,setPrefixes]=useState('/'),[excluded,setExcluded]=useState(''),[sitemaps,setSitemaps]=useState(false);
 const [records,setRecords]=useState<Row[]>([]),[summary,setSummary]=useState(''),[history,setHistory]=useState<any[]>([]);
 function changed(){setConsent(false);setPaths(null);setChosen([]);setRecords([]);setSummary('')}
 async function discover(){setBusy(true);setError('');setPaths(null);setChosen([]);setRecords([]);try{
  const result=await api(`/assets/${assetId}/discover-recursive`,'POST',{accepted:consent,max_pages:budget,max_depth:depth,max_seconds:20,prefixes:prefixes.split('\n').map(p=>p.trim()).filter(Boolean),excluded:excluded.split('\n').map(p=>p.trim()).filter(Boolean),sitemaps});
  setPaths(result.paths);setRecords(result.records||[]);setSummary(`${result.requests_performed} requests. ${result.budget_exhausted?'Stopped at a safety budget; more pages may exist.':'Discovery finished.'}`);
 }catch(e){setError((e as Error).message)}finally{setBusy(false);setConsent(false)}}
 return <section aria-label="Recursive page discovery"><h4>Discover nested website pages</h4><p className="subtle">Follow public links within your approved path prefixes. Maximum 20 requests, one per second, with a 20-second traversal budget. No redirects, query strings, authenticated areas, forms or JavaScript. Assessment requires separate approval.</p>
 <fieldset disabled={busy}><label>Maximum discovery requests<input type="number" min={1} max={20} value={budget} onChange={e=>{setBudget(Number(e.target.value));changed()}}/></label>
 <label>Maximum discovery depth<input type="number" min={0} max={5} value={depth} onChange={e=>{setDepth(Number(e.target.value));changed()}}/></label>
 <label>Approved path prefixes (one per line)<textarea value={prefixes} onChange={e=>{setPrefixes(e.target.value);changed()}}/></label>
 <label>Excluded path prefixes (one per line)<textarea value={excluded} onChange={e=>{setExcluded(e.target.value);changed()}}/></label>
 <label className="check"><input type="checkbox" checked={sitemaps} onChange={e=>{setSitemaps(e.target.checked);changed()}}/>Include XML sitemaps within this scope and request budget.</label>
 <label className="check"><input type="checkbox" checked={consent} disabled={!verified} onChange={e=>setConsent(e.target.checked)}/>I authorize recursive GET discovery within these prefixes, exclusions and limits.</label></fieldset>
 <button disabled={!verified||!consent||busy||budget<1||budget>20||depth<0||depth>5||!prefixes.trim()} onClick={discover}>{busy?'Discovering approved pages…':'Discover nested pages'}</button>
 <button disabled={busy} onClick={async()=>{try{setHistory(await api(`/assets/${assetId}/discovery-history`))}catch(e){setError((e as Error).message)}}}>Load discovery history</button>
 {history.map(h=><p key={h.id}>{new Date(h.created*1000).toLocaleString()} · {h.scope.result?`${h.scope.result.paths.length} pages, ${h.scope.result.requests_performed} requests`:'Stopped or incomplete'} · {h.active?'Active':'Ended'}</p>)}
 {busy&&<p role="status">Revoke this asset’s authorization to stop further discovery requests.</p>}{error&&<p role="alert" className="error">{error}</p>}
 {paths!==null&&<><p role="status">{paths.length} candidate paths. Select up to 20. {summary}</p>
 {paths.map(path=><label className="check" key={path}><input type="checkbox" checked={chosen.includes(path)} onChange={e=>setChosen(e.target.checked?[...chosen,path]:chosen.filter(p=>p!==path))}/>{path}</label>)}
 <button disabled={!chosen.length} onClick={()=>onSelect(chosen)}>Use discovered paths for review</button>
 <details><summary>Discovery evidence and skipped pages</summary>{records.map((r,i)=><p key={i}>{r.path} · depth {r.depth} · {r.source} · {r.status.replaceAll('_',' ')}</p>)}</details></>}
 </section>
}
