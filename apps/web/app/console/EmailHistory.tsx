'use client';
import {useState} from 'react';
export default function EmailHistory({api,org}:{api:(p:string)=>Promise<any>;org:string}){
 const [rows,setRows]=useState<any[]>([]),[error,setError]=useState('');
 return <section><h4>Your email delivery history</h4><p>SMTP accepted means the mail server accepted the message. Inbox delivery is not confirmed. Retries use the same message identifier; a server timeout can still cause duplicate delivery.</p><button onClick={async()=>{try{setRows(await api(`/organizations/${org}/email-history`));setError('')}catch(e){setError((e as Error).message)}}}>Refresh email history</button>{error&&<p role="alert">{error}</p>}{rows.map(r=><div className="row" key={r.id}>{r.title} · {r.status} · {r.attempts} attempts {r.error}</div>)}</section>
}
