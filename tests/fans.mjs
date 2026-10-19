import {chromium} from 'playwright';
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';

const base=process.env.BASE_URL||'http://127.0.0.1:4173';
const output=process.env.FAN_REPORT||'qa/fan-animation-report.json';
const anchors=JSON.parse(fs.readFileSync('blender/viewer-anchors.json')).rotors;
const report={passed:false,url:base,checkedAt:new Date().toISOString(),checks:[],errors:[],network:[],sourceHashesAtStart:Object.fromEntries(['src/app.js','assets/campus.glb','blender/viewer-anchors.json'].map(file=>[file,crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')]))};
const check=(name,value)=>{assert.ok(value,name);report.checks.push(name);};
const browser=await chromium.launch({channel:'chrome',headless:true});
const watch=page=>{page.on('pageerror',e=>report.errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)report.network.push({url:r.url(),status:r.status()});});};
const ready=page=>page.waitForFunction(()=>window.SEED?.ready&&!SEED.state.flying&&!document.querySelector('#loading'));
const sample=page=>page.evaluate(async()=>{
 const names=['coolerRotorInstances','chillerRotorInstances'];
 const snapshot=()=>names.map(name=>({name,count:SEED.groups[name].count,matrices:Array.from(SEED.groups[name].instanceMatrix.array)}));
 let last=await new Promise(requestAnimationFrame),elapsed=0;
 // Re-snapshot at the same frame timestamp used as the measurement origin.
 const first=snapshot();
 for(let i=0;i<8;i++){const now=await new Promise(requestAnimationFrame);elapsed+=Math.min(.05,(now-last)/1000);last=now;}
 return {first,after:snapshot(),elapsed};
});
function inspectMotion(sample,expectedSpeed,label){
 for(const [b,first] of sample.first.entries()){
  const after=sample.after[b],angles=[],fixed=[];
  for(let i=0;i<first.count;i++){
   const a=first.matrices.slice(i*16,i*16+16),z=after.matrices.slice(i*16,i*16+16);
   fixed.push([12,13,14].every(k=>Math.abs(a[k]-z[k])<1e-5));
   const change=Math.atan2(Math.sin(Math.atan2(z[8],z[0])-Math.atan2(a[8],a[0])),Math.cos(Math.atan2(z[8],z[0])-Math.atan2(a[8],a[0])));
   angles.push(Math.abs(change)/sample.elapsed);
  }
  check(`${label}: every ${first.name} blade stays at its hub`,fixed.every(Boolean));
  check(`${label}: every ${first.name} blade turns at expected illustrative speed`,angles.every(rate=>Math.abs(rate-expectedSpeed)<.002));
 }
}
try{
 const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'no-preference'});watch(page);
 await page.goto(`${base}/?render=1#stop-5`);await ready(page);
 const scene=await page.evaluate(()=>SEED.inspect());
 check('All 816 dry cooler and 42 chiller fans are present',JSON.stringify(scene.fans)===JSON.stringify([{name:'coolerRotorInstances',count:816},{name:'chillerRotorInstances',count:42}]));
 check('Fan rendering remains batched, below 220 draw calls',scene.drawCalls<220);report.render=scene.fans;report.drawCalls=scene.drawCalls;
 const summer=await sample(page);inspectMotion(summer,Math.PI*2,'Summer');
 for(const batch of summer.first){
  const prefix=batch.name.replace('Instances','');
  const expected=Object.entries(anchors).filter(([name])=>new RegExp('^'+prefix+'\\d+$').test(name)).map(([,p])=>[p[0],p[2],-p[1]]);
  const actual=Array.from({length:batch.count},(_,i)=>batch.matrices.slice(i*16+12,i*16+15));
  check(`${prefix}: every pivot matches the saved Blender geometry`,actual.every(p=>expected.some(q=>q.every((v,i)=>Math.abs(v-p[i])<.001))));
  check(`${prefix}: all pivots are distinct`,new Set(actual.map(p=>p.map(v=>v.toFixed(3)).join(','))).size===expected.length);
 }
 const hits=await page.evaluate(async()=>{
  const T=await import('/vendor/three/three.module.js');SEED.scene.updateMatrixWorld(true);
  return ['coolerRotorInstances','chillerRotorInstances'].map(name=>{
   const mesh=SEED.groups[name],m=new T.Matrix4();mesh.getMatrixAt(0,m);
   const blade=new T.Vector3(.2,0,0).applyMatrix4(m).applyMatrix4(mesh.matrixWorld);
   const ray=new T.Raycaster(blade.clone().add(new T.Vector3(0,5,0)),new T.Vector3(0,-1,0));
   const hit=ray.intersectObject(mesh)[0];return {name,id:hit?.object.userData.objectId,instance:hit?.instanceId};
  });
 });
 check('Both fan batches remain pickable as their equipment',hits[0].id==='coolers'&&hits[1].id==='chillers'&&hits.every(h=>h.instance===0));
 await page.evaluate(()=>SEED.view([14,23,28],[0,43,9]));await sample(page);await page.screenshot({path:'qa/fans-coolers.png'});
 await page.evaluate(()=>SEED.view([128,27,18],[119,43,2]));await sample(page);await page.screenshot({path:'qa/fans-chillers.png'});
 await page.evaluate(()=>SEED.setToggle('winter'));inspectMotion(await sample(page),Math.PI*.5,'Winter');
 await page.close();
 const reduced=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});watch(reduced);
 await reduced.goto(`${base}/#stop-5`);await ready(reduced);
 const paused=await sample(reduced);check('Reduced motion pauses every one of the 858 fans',JSON.stringify(paused.first)===JSON.stringify(paused.after));
 await reduced.locator('#tab-freeze').click();
 const cold=reduced.locator('#panel-freeze details').filter({hasText:'Does computer heat make a cold snap harmless?'}).first();
 await cold.locator('summary').click();await cold.scrollIntoViewIfNeeded();
 check('Visible cold snap explanation states the uncalculated heat balance',(await cold.innerText()).includes('has not yet calculated the worst-case cold-snap heat balance'));
 await reduced.screenshot({path:'qa/fans-winter-explanation.png'});
 check('No browser errors',!report.errors.length);check('No failed assets',!report.network.length);report.passed=true;
}catch(e){report.failure=String(e);console.error(e);process.exitCode=1;}
finally{await browser.close();fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,checks:report.checks.length,drawCalls:report.drawCalls,failure:report.failure}));}
