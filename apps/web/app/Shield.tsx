'use client';
import {useEffect, useRef} from 'react';
export default function Shield(){
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{let cleanup=()=>{};let cancelled=false;
 if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
 import('three').then(T=>{if(cancelled || !ref.current) return; try{
 const host=ref.current,scene=new T.Scene(),camera=new T.PerspectiveCamera(35,1,.1,100);camera.position.z=6;
 const renderer=new T.WebGLRenderer({alpha:true,antialias:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.5));renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();host.appendChild(renderer.domElement);
 const group=new T.Group();scene.add(group);
 const sphere=new T.Mesh(new T.IcosahedronGeometry(1.7,2),new T.MeshBasicMaterial({color:0x54dfec,wireframe:true,transparent:true,opacity:.13}));group.add(sphere);
 const shape=new T.Shape();shape.moveTo(0,1);shape.lineTo(.8,.65);shape.lineTo(.65,-.35);shape.quadraticCurveTo(.4,-.85,0,-1.1);shape.quadraticCurveTo(-.4,-.85,-.65,-.35);shape.lineTo(-.8,.65);shape.closePath();
 const shield=new T.Mesh(new T.ExtrudeGeometry(shape,{depth:.16,bevelEnabled:true,bevelSegments:3,steps:1,bevelSize:.06,bevelThickness:.06}),new T.MeshPhysicalMaterial({color:0x47dcdb,metalness:.6,roughness:.2,transparent:true,opacity:.85}));group.add(shield);
 scene.add(new T.AmbientLight(0x8aabff,2));const light=new T.PointLight(0x74ffff,40);light.position.set(2,3,4);scene.add(light);
 let visible=true;const observer=typeof IntersectionObserver!=='undefined'?new IntersectionObserver(entries=>{visible=entries[0]?.isIntersecting??false}):null;observer?.observe(host);
 let frame=0,last=0;const render=(t:number)=>{frame=requestAnimationFrame(render);if(document.hidden||!visible||t-last<33)return;last=t;sphere.rotation.y=t*.00012;shield.rotation.y=Math.sin(t*.0004)*.25;group.position.y=Math.sin(t*.0006)*.08;renderer.render(scene,camera)};frame=requestAnimationFrame(render);
 const resize=()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix()};window.addEventListener('resize',resize);
 cleanup=()=>{observer?.disconnect();cancelAnimationFrame(frame);window.removeEventListener('resize',resize);sphere.geometry.dispose();sphere.material.dispose();shield.geometry.dispose();shield.material.dispose();renderer.dispose();renderer.domElement.remove()};
 }catch{/* Static CSS shield remains available if WebGL is unavailable. */}}).catch(()=>{/* Keep static fallback when the optional chunk cannot load. */});return()=>{cancelled=true;cleanup()};},[]);
 return <div className="scene" ref={ref} aria-label="Protective shield visualization"><div className="static-shield">◇</div></div>
}
