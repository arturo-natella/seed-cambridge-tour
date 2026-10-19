import {chromium} from 'playwright';import fs from 'node:fs';import assert from 'node:assert/strict';
const content=JSON.parse(fs.readFileSync('assets/content.json','utf8'));const report={checks:[],errors:[],network:[],screenshots:[]};
const browser=await chromium.launch({channel:'chrome',headless:true});const page=await browser.newPage({viewport:{width:1920,height:1080}});
page.on('pageerror',e=>report.errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)report.network.push({url:r.url(),status:r.status()})});
const check=(name,value)=>{assert.ok(value,name);report.checks.push(name);};
const settled=()=>page.waitForFunction(()=>SEED.ready&&!SEED.state.flying&&!document.querySelector('#story').classList.contains('pending')&&parseFloat(getComputedStyle(document.querySelector('#story')).opacity)>.99);
try{
 await page.goto('http://127.0.0.1:4173');await page.waitForFunction(()=>window.SEED?.ready);await settled();
 for(let i=0;i<13;i++){
  await settled();const b=content.bubbles[i];check(`Card ${i}: exact headline`,await page.locator('#headline').textContent()===b.headline);
  check(`Card ${i}: exact bullets`,JSON.stringify(await page.locator('#bullets li').allTextContents())===JSON.stringify(b.bullets));
  check(`Card ${i}: exact number and unit`,await page.locator('#number').textContent()===b.number&&await page.locator('#unit').textContent()===b.unit);
  check(`Card ${i}: source tag`,await page.locator('#source').textContent()===b.source);
  if(b.assumption&&!b.hideOverviewAssumption){check(`Card ${i}: assumption visible`,await page.locator('#assumption').isVisible());check(`Card ${i}: exact assumption`,await page.locator('#assumption p').textContent()===b.assumption.replace(/^…/,''));}
  if(b.referenceModels){check(`Card ${i}: reference models visible`,await page.locator('#reference-models').isVisible());for(const m of b.referenceModels)check(`Card ${i}: ${m.name} reference`,(await page.locator('#reference-models').textContent()).includes(m.name));}
  const bounds=await page.locator('#story').evaluate(e=>({scroll:e.scrollHeight,client:e.clientHeight,rect:{top:e.getBoundingClientRect().top,bottom:e.getBoundingClientRect().bottom}}));check(`Card ${i}: fits 1080p`,bounds.scroll<=bounds.client+2&&bounds.rect.top>=95&&bounds.rect.bottom<=970);
  const file=`qa/stop-${String(i).padStart(2,'0')}.png`;await page.screenshot({path:file});report.screenshots.push(file);
  await page.locator('#more').click();check(`Stop ${i}: choice stays in main card`,await page.locator('#panel-why').isVisible()&&await page.evaluate(()=>SEED.state.index)===i);
  check(`Stop ${i}: exact choice reason`,await page.locator('#choice-why').textContent()===b.why);
  if(b.card){for(const k of ['what','how'])check(`Stop ${i}: ${k} detail`,(await page.locator('#choice-details').textContent()).includes(b.card[k]));await page.locator('#choice-details summary').click();for(const m of b.card.math)check(`Stop ${i}: local calculation`,(await page.locator('.math-notes').textContent()).includes(m));}
  const design=page.locator('#choice-design > details').first();await design.locator(':scope > summary').click();check(`Stop ${i}: local design expanded`,await design.locator('.design-copy').isVisible());check(`Stop ${i}: source notes included`,await design.locator('.source-notes').count()===1);
  if(i===7){await page.screenshot({path:'qa/greenhouse-choice.png'});report.screenshots.push('qa/greenhouse-choice.png');}
  await page.locator('#tab-closer').click();check(`Stop ${i}: closer look in main card`,await page.locator('#panel-closer').isVisible());check(`Stop ${i}: relevant equipment first`,await page.locator('#object-select').inputValue()===b.objectKeys[0]);
  await page.locator('#card-prev').click();check(`Stop ${i}: carousel previous`,await page.locator('#panel-why').isVisible());await page.locator('#card-next').click();await page.locator('#card-next').click();
  if(b.referenceModels||[4,5,6,9].includes(i)){const extra=b.referenceModels?'energy':i===6?'geothermal':'freeze';check(`Stop ${i}: ${extra} card in carousel`,await page.locator('#panel-'+extra).isVisible());await page.locator('#card-next').click();}
  check(`Stop ${i}: carousel wraps`,await page.locator('#panel-overview').isVisible());
  await page.locator('#viewport canvas').focus();
  if(i<12){if(i%3===0)await page.keyboard.press('PageDown');else if(i%3===1)await page.keyboard.press('ArrowRight');else await page.locator('#next').click();}
 }
 await page.keyboard.press('PageUp');await settled();check('Clicker goes backward',await page.evaluate(()=>SEED.state.index)===11);
 await page.keyboard.press('Home');await settled();
 await page.locator('#index-toggle').click();await page.locator('#stop-list nav button').nth(3).click();await settled();check('Stop list jumps to hall',await page.evaluate(()=>SEED.state.index===3&&SEED.state.xray&&!SEED.groups.hall.visible&&!SEED.groups.hallRoof.visible));
 await page.locator('#toggle-xray').click();check('X-ray restores shell',await page.evaluate(()=>SEED.groups.hall.visible));await page.locator('#toggle-xray').click();
 await page.locator('#toggle-ground').click();check('Cutaway exposes actual loops',await page.evaluate(()=>SEED.groups.boreholes.visible&&!SEED.groups.groundCap.visible&&!SEED.groups.solarField.visible));await page.locator('#toggle-ground').click();
 await page.locator('#toggle-flow').click();check('Interior system color key visible',await page.locator('#scene-key').isVisible());
 await page.locator('#toggle-season').click();check('Winter active',await page.locator('#season-label').textContent()==='Winter');await page.locator('#toggle-season').click();
 await page.locator('#toggle-labels').click();check('Labels enabled',await page.evaluate(()=>SEED.state.labels));
 await page.mouse.move(1300,600);await page.mouse.down();await page.mouse.move(1400,630,{steps:10});await page.mouse.up();check('Orbit tucks the cue card',await page.locator('#story').evaluate(e=>e.classList.contains('tucked')));await page.locator('#next').click();await settled();check('Next resumes after exploration',await page.evaluate(()=>SEED.state.index===4&&!SEED.state.exploring));
 // Verify every equipment explanation, local design and optional source citation.
 for(const [key,o] of Object.entries(content.objects)){
  await page.evaluate(k=>SEED.openObject(k),key);check(`Object ${key}: exact text`,(await page.locator('#object-description').textContent()).replace(/\s+/g,' ').includes(o.text.replace(/\*/g,'').replace(/\s+/g,' ')));
  check(`Object ${key}: selected in carousel`,await page.locator('#panel-closer').isVisible()&&await page.locator('#object-select').inputValue()===key);
  check(`Object ${key}: math URL`,await page.locator('#object-design > a').getAttribute('href')===content.mathURL+o.math);
  const design=page.locator('#object-design > details');await design.locator(':scope > summary').click();check(`Object ${key}: design details local`,await design.locator('.design-copy').isVisible());
 }
 await page.locator('#object-select').selectOption('greenhouse');check('Equipment selector changes detail',await page.locator('#object-title').textContent()===content.objects.greenhouse.name);await page.screenshot({path:'qa/greenhouse-closer.png'});
 await page.locator('#tab-overview').click();await page.locator('#tab-overview').focus();const stopBefore=await page.evaluate(()=>SEED.state.index);await page.keyboard.press('ArrowRight');check('Tab keyboard changes card without changing stop',await page.locator('#panel-why').isVisible()&&await page.evaluate(()=>SEED.state.index)===stopBefore);
 await page.evaluate(()=>{if(SEED.state.labels)SEED.setToggle('labels')});
 // Real mesh hover/click, independently raycast from model geometry to visible screen points.
 const stops={hall:0,roofSolar:0,sealed:3,compute:3,network:3,trench:3,fire:3,spine:4,electrical:3,bridges:5,coolers:5,chillers:5,boreholes:6,batteryHouse:6,solar:2,substation:8,generators:9,fuel:9,reserved:9,house:1,greenhouse:7,snowpad:0,dewpoint:3,freshAir:4,airlock:3,bypass:5,freezeProtection:5,drainTanks:4,coldInsulation:6};
 for(const [key,stop] of Object.entries(stops)){
  await page.evaluate(({stop,key})=>{SEED.goTo(stop,true);if(['dewpoint','freshAir','airlock','bypass','freezeProtection','drainTanks','coldInsulation'].includes(key))SEED.focusSystem(key);if(key==='batteryHouse'&&SEED.state.ground)SEED.setToggle('ground');if(key==='bridges')SEED.view([-20,12,19],[0,33,7]);if(key==='chillers')SEED.view([157,12,23],[123,48,2]);}, {stop,key});await settled();
  const point=await page.evaluate(async key=>{
   const T=await import('/vendor/three/three.module.js');const alias={hallRoof:'hall',partitions:'sealed',spares:'compute',power:'electrical',powerLine:'substation',heatPipes:'spine',geology:'boreholes',groundCap:'boreholes',parking:'solar',solarField:'solar'};
   function id(o){while(o){if(o.userData.objectId){const k=alias[o.userData.objectId]||o.userData.objectId;if(SEED.content.objects[k])return k;}o=o.parent;}return null}
   function vis(o){while(o){if(!o.visible)return false;o=o.parent;}return true}
   let all=[];SEED.scene.traverse(o=>{if(o.isMesh&&vis(o)&&o.geometry?.attributes.position)all.push(o)});SEED.scene.updateMatrixWorld(true);
   const target=all.filter(o=>id(o)===key),ray=new T.Raycaster(),vec=new T.Vector3();
   const story=document.querySelector('#story').getBoundingClientRect();
   // Validate the exact screen pixel that the pointer will click. A projected
   // vertex can otherwise round onto a neighboring rack or pipe at its edge.
   function tryPoint(vec){const p=vec.clone().project(SEED.camera),x=Math.round((p.x+1)*innerWidth/2),y=Math.round((1-p.y)*innerHeight/2);if(p.z>1||x<story.right+20||x>innerWidth-220||y<115||y>innerHeight-125||document.elementFromPoint(x,y)!==SEED.renderer.domElement)return null;ray.setFromCamera(new T.Vector2(x/innerWidth*2-1,1-y/innerHeight*2),SEED.camera);const first=ray.intersectObjects(all,false)[0];return first&&id(first.object)===key?{x,y}:null;}
   const anchor=SEED.anchors[key];if(anchor){const p=tryPoint(new T.Vector3(anchor[0],anchor[2],-anchor[1]));if(p)return p;}
   for(const o of target){const a=o.geometry.attributes.position;for(let i=0;i<a.count;i+=Math.max(1,Math.floor(a.count/160))){vec.fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld);const p=tryPoint(vec);if(p)return p;}}
   return null;
  },key);
  check(`Object ${key}: reachable in model`,!!point);
  await page.mouse.move(700,200);await page.mouse.move(point.x,point.y);await page.waitForTimeout(200);check(`Mesh ${key}: hover`,await page.locator('#tooltip').isVisible());await page.mouse.click(point.x,point.y);check(`Mesh ${key}: real click`,await page.locator('#object-title').textContent()===content.objects[key].name&&await page.locator('#panel-closer').isVisible());
 }
 // Measure actual frame cadence on the complete model, not an empty canvas.
 await page.evaluate(()=>SEED.goTo(0,true));await settled();report.performance=await page.evaluate(()=>new Promise(resolve=>{const samples=[];let previous;function frame(t){if(previous)samples.push(t-previous);previous=t;if(samples.length<90)requestAnimationFrame(frame);else{samples.sort((a,b)=>a-b);resolve({medianMs:samples[45],p95Ms:samples[85],drawCalls:SEED.renderer.info.render.calls,triangles:SEED.renderer.info.render.triangles});}}requestAnimationFrame(frame)}));
 await page.setViewportSize({width:1366,height:768});await page.evaluate(()=>SEED.goTo(6,true));await settled();await page.screenshot({path:'qa/laptop.png'});check('Laptop: assumption readable',await page.locator('#assumption').isVisible());
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>SEED.goTo(0,true));await settled();await page.screenshot({path:'qa/mobile.png'});check('Mobile: no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth===innerWidth));
 await page.locator('#tab-why').click();check('Mobile: choice can scroll',await page.locator('#panel-why').evaluate(e=>e.clientHeight>70));await page.locator('#tab-closer').click();await page.locator('#object-select').selectOption('greenhouse');check('Mobile: equipment selector works',await page.locator('#object-title').textContent()===content.objects.greenhouse.name);await page.screenshot({path:'qa/mobile-closer.png'});
 check('Card browsing never opens another page',browser.contexts()[0].pages().length===1);
 check('No browser errors',report.errors.length===0);check('No failed asset loads',report.network.length===0);report.passed=true;
}catch(e){report.passed=false;report.failure=String(e);console.error(e);await page.screenshot({path:'qa/test-failure.png'});}finally{fs.writeFileSync('qa/browser-report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify({passed:report.passed,checks:report.checks.length,performance:report.performance,failure:report.failure}));if(!report.passed)process.exitCode=1;}
