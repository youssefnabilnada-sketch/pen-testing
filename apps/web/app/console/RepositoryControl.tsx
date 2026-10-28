'use client';
import {useEffect,useState} from 'react';
type API=(path:string,method?:string,data?:unknown)=>Promise<any>;
export default function RepositoryControl({api}:{api:API}){
 const [paused,setPaused]=useState<boolean|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let active=true;api('/admin/repository-control').then(r=>{if(active)setPaused(r.paused)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[api]);
 async function change(){setBusy(true);setError('');try{const r=await api('/admin/repository-control','POST',{accepted:!paused});setPaused(r.paused)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <section className="glass panel"><h3>Repository publication control</h3><p>{paused===null?'Publication state unavailable':paused?'New pull request publication is paused':'Reviewed pull request publication is enabled'}</p><p className="subtle">Pausing blocks new publication requests. It does not undo remote operations already in progress or merge any changes.</p>{error&&<p role="alert">{error}</p>}<button disabled={busy||paused===null} onClick={change}>{paused?'Resume reviewed publication':'Pause new publication'}</button></section>
}
