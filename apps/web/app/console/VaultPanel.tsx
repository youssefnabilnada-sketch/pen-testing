'use client';
import {useEffect,useState} from 'react';

type VaultItem={id:string;job_id:string;integrity:string;profile?:string;legal_hold:boolean};
type VaultData={retention:string;integrity_limit:string;items:VaultItem[]};
type Api=(path:string,method?:string,data?:unknown)=>Promise<any>;

export default function VaultPanel({api,org,role}:{api:Api;org:string;role:string}){
 const [data,setData]=useState<VaultData|null>(null);
 const [error,setError]=useState('');
 const [notice,setNotice]=useState('');
 const [selected,setSelected]=useState<string|null>(null);
 const [reason,setReason]=useState('');
 const [busy,setBusy]=useState(false);
 const editable=role==='owner'||role==='admin';
 useEffect(()=>{
  let active=true;
  setSelected(null);setReason('');setNotice('');setError('');setData(null);
  api(`/organizations/${org}/evidence-vault`)
   .then((r:VaultData)=>{if(active)setData(r)})
   .catch((e:Error)=>{if(active)setError(e.message)});
  return()=>{active=false};
 },[api,org]);
 async function updateHold(item:VaultItem){
  if(!editable||busy||reason.trim().length<8)return;
  setBusy(true);setError('');setNotice('');
  try{
   const method=item.legal_hold?'release':'';
   await api(`/evidence-vault/${item.id}/legal-hold${method?'/release':''}`,'POST',{reason:reason.trim()});
   setData(await api(`/organizations/${org}/evidence-vault`));
   setSelected(null);setReason('');
   setNotice(item.legal_hold?'Legal hold released. Evidence remains retained.':'Legal hold placed. Evidence will be preserved.');
  }catch(e){setError(e instanceof Error?e.message:'The hold could not be updated.');}
  finally{setBusy(false);}
 }
 return <section className="glass panel"><h3>Evidence Vault</h3>
  {error&&<p role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
  {data&&<><p>{data.retention}</p><p>{data.integrity_limit}</p>
   <p className="subtle">Legal holds preserve evidence for review. Releasing a hold does not delete evidence.</p>
   {data.items.map(item=><div key={item.id}>
    <div className="row"><div className="grow">Assessment {item.job_id} · {item.integrity} · {item.profile}
     {item.legal_hold&&<strong> · Legal hold active</strong>}
    </div>
     {item.integrity!=='mismatch'&&<a className="button" href={`/api/evidence-vault/${item.id}/export`}>Export evidence JSON</a>}
     {editable&&<button type="button" onClick={()=>{setSelected(selected===item.id?null:item.id);setReason('');setError('')}}>
      {item.legal_hold?'Release hold':'Place legal hold'}
     </button>}
    </div>
    {selected===item.id&&editable&&<form className="form" onSubmit={e=>{e.preventDefault();void updateHold(item)}}>
     <label>{item.legal_hold?'Reason for releasing the hold':'Reason to preserve this report'}
      <textarea required minLength={8} maxLength={500} value={reason} onChange={e=>setReason(e.target.value)}/>
     </label>
     <div className="actions"><button disabled={busy||reason.trim().length<8} type="submit">
      {busy?'Saving…':item.legal_hold?'Confirm release (no deletion)':'Confirm legal hold'}</button>
      <button type="button" disabled={busy} onClick={()=>{setSelected(null);setReason('')}}>Cancel</button>
     </div>
    </form>}
   </div>)}
  </>}
 </section>;
}
