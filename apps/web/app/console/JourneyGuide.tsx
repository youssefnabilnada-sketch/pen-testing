'use client';
import {ArrowRight,CheckCircle2,Globe,ShieldCheck,ScanLine,FileSearch} from 'lucide-react';

type Stage={title:string;description:string;page:string;done:boolean;icon:typeof Globe};
export default function JourneyGuide({assets,verified,completed,onNavigate}:{
 assets:number;verified:number;completed:number;onNavigate:(page:string)=>void
}){
 const stages:Stage[]=[
  {title:'Add your website',description:'Register the exact website you control.',page:'Assets',done:assets>0,icon:Globe},
  {title:'Prove ownership',description:'Choose a simple verification method for your hosting provider.',page:'Assets',done:verified>0,icon:ShieldCheck},
  {title:'Run an authorized scan',description:'Review scope and approve safe checks before scanning.',page:'Assets',done:completed>0,icon:ScanLine},
  {title:'Review findings & fixes',description:'Read evidence, download reports and request approved fixes.',page:'Findings',done:completed>0,icon:FileSearch}
 ];
 const next=stages.findIndex(s=>!s.done);
 return <section className="journey-guide glass" aria-label="Getting started with AEGIS">
   <div className="journey-heading">
     <div><p className="eyebrow">GET STARTED • 4 STEPS</p><h2>Know what to do next.</h2><p>Follow one clear path from your first website to an actionable security report.</p></div>
     <span className="journey-progress" role="status">{stages.filter(s=>s.done).length} of 4 completed</span>
   </div>
   <div className="journey-grid">
     {stages.map((stage,i)=>{
       const Icon=stage.icon;
       return <div className={'journey-step '+(stage.done?'is-done':i===next?'is-next':'')} key={stage.title}>
         <div className="journey-index">{stage.done?<CheckCircle2 aria-label="Complete" size={17}/>:<Icon aria-hidden size={17}/>}<span>STEP {i+1}</span></div>
         <strong>{stage.title}</strong><p>{stage.description}</p>
         <button type="button" onClick={()=>onNavigate(stage.page)} aria-label={stage.done?'Review '+stage.title:'Continue to '+stage.title}>
           {stage.done?'Review':i===next?'Continue':'Explore'} <ArrowRight size={14} aria-hidden/>
         </button>
       </div>
     })}
   </div>
   <p className="journey-safety">A website must be verified and explicitly authorized before an assessment. A request for a fix never changes a customer website automatically.</p>
 </section>;
}
