import {chromium} from 'playwright';
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';

const content=JSON.parse(fs.readFileSync('assets/content.json','utf8'));
const newEquipment=['bypass','freezeProtection','drainTanks','coldInsulation','freshAir','airlock','dewpoint'];
const report={passed:false,checks:[],errors:[],network:[],screenshots:[],sourceHashesAtStart:Object.fromEntries(['src/app.js','src/style.css','assets/content.json','assets/campus.glb'].map(file=>[file,crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')]))};
const browser=await chromium.launch({channel:'chrome',headless:true});
const context=await browser.newContext({viewport:{width:1920,height:1080},reducedMotion:'reduce'});
const page=await context.newPage();
page.on('pageerror',error=>report.errors.push(String(error)));
page.on('response',response=>{if(response.status()>=400)report.network.push({url:response.url(),status:response.status()});});
const check=(name,pass)=>{assert.ok(pass,name);report.checks.push(name);};
const settled=()=>page.waitForFunction(()=>window.SEED?.ready&&!SEED.state.flying&&!document.querySelector('#story').classList.contains('pending')&&Number(getComputedStyle(document.querySelector('#story')).opacity)>.99);
const atStop=async stop=>{await page.evaluate(stop=>SEED.goTo(stop,true),stop);await settled();};
const capture=async name=>{const file=`qa/thermal-design-${name}.png`;await page.screenshot({path:file});report.screenshots.push(file);};
const noOverflow=async(name,panel)=>check(name,await page.locator(panel).evaluate(element=>document.documentElement.scrollWidth<=innerWidth+1&&element.scrollWidth<=element.clientWidth+1&&document.querySelector('#story').scrollWidth<=document.querySelector('#story').clientWidth+1));
const snapshotOverview=()=>page.evaluate(()=>({headline:document.querySelector('#headline').textContent,source:document.querySelector('#source').textContent,overview:document.querySelector('#panel-overview').innerText}));
const actualMeshPoint=key=>page.evaluate(async key=>{
 const T=await import('/vendor/three/three.module.js');
 const visible=object=>{while(object){if(!object.visible)return false;object=object.parent;}return true;};
 const objectId=object=>{while(object){if(object.userData.objectId)return object.userData.objectId;object=object.parent;}return null;};
 SEED.scene.updateMatrixWorld(true);
 const all=[];SEED.scene.traverse(object=>{if(object.isMesh&&visible(object)&&object.geometry?.attributes.position)all.push(object);});
 const targets=all.filter(object=>objectId(object)===key),ray=new T.Raycaster();
 function tryPoint(position){
  const p=position.clone().project(SEED.camera),x=Math.round((p.x+1)*innerWidth/2),y=Math.round((1-p.y)*innerHeight/2);
  if(p.z>1||x<15||x>innerWidth-15||y<100||y>innerHeight-110||document.elementFromPoint(x,y)!==SEED.renderer.domElement)return null;
  ray.setFromCamera(new T.Vector2(x/innerWidth*2-1,1-y/innerHeight*2),SEED.camera);const hit=ray.intersectObjects(all,false)[0];
  return hit&&objectId(hit.object)===key?{x,y}:null;
 }
 const anchor=SEED.anchors[key];if(anchor){const result=tryPoint(new T.Vector3(anchor[0],anchor[2],-anchor[1]));if(result)return result;}
 for(const object of targets){
  const box=new T.Box3().setFromObject(object),center=box.getCenter(new T.Vector3()),first=tryPoint(center);if(first)return first;
  const vertices=object.geometry.attributes.position;
  for(let i=0;i<vertices.count;i+=Math.max(1,Math.floor(vertices.count/450))){const result=tryPoint(new T.Vector3().fromBufferAttribute(vertices,i).applyMatrix4(object.matrixWorld));if(result)return result;}
 }
 return null;
},key);

try{
 await page.goto('http://127.0.0.1:4173/#stop-6');await settled();
 check('All 29 requested equipment explanations are available',Object.keys(content.objects).length===29);
 for(const viewport of [{name:'desktop',width:1920,height:1080},{name:'laptop',width:1366,height:768},{name:'phone',width:390,height:844}]){
  await page.setViewportSize({width:viewport.width,height:viewport.height});
  for(let stop=0;stop<13;stop++){
   await atStop(stop);
   const visibleTabs=await page.locator('.card-tabs button:visible').evaluateAll(elements=>elements.map(element=>element.id));
   const special=stop===6?'geothermal':[4,5,9].includes(stop)?'freeze':[0,3,8,10,11,12].includes(stop)?'energy':null;
   check(`${viewport.name} stop ${stop}: only the relevant fourth card is available`,visibleTabs.join(',')===['tab-overview','tab-why','tab-closer',...(special?['tab-'+special]:[])].join(','));
  }
  await atStop(6);const original=await snapshotOverview(),url=page.url();
  await page.locator('#show-system').click();
  check(`${viewport.name}: ground explanation stays in the main card`,await page.locator('#panel-geothermal').isVisible()&&page.url()===url);
  await page.locator('#geo-summer').click();
  const summerArrow=await page.locator('#geo-season svg path[fill="#d85a30"]').getAttribute('d');
  check(`${viewport.name}: summer moves heat into rock through sealed fluid`,(await page.locator('#geo-season svg').getAttribute('aria-label')).includes('sealed U-pipe into rock')&&await page.evaluate(()=>!SEED.state.winter)&&await page.locator('#geo-summer').getAttribute('aria-pressed')==='true');
  await page.locator('#geo-season svg').scrollIntoViewIfNeeded();await capture(`${viewport.name}-summer`);
  await page.locator('#geo-winter').click();
  const winterArrow=await page.locator('#geo-season svg path[fill="#d85a30"]').getAttribute('d');
  check(`${viewport.name}: winter changes diagram and global season together`,winterArrow!==summerArrow&&await page.evaluate(()=>SEED.state.winter)&&await page.locator('#season-label').textContent()==='Winter'&&await page.locator('#geo-winter').getAttribute('aria-pressed')==='true');
  check(`${viewport.name}: winter explanation excludes air entering boreholes`,(await page.locator('#geo-season svg').getAttribute('aria-label')).includes('no air enters the borehole')&&(await page.locator('#geo-season').innerText()).includes('separate from supplying the warm hall circuit'));
  check(`${viewport.name}: season controls preserve card and route`,page.url()===url&&await page.evaluate(()=>SEED.state.index===6&&SEED.state.card===3));
  await page.locator('#geo-season svg').scrollIntoViewIfNeeded();await capture(`${viewport.name}-winter`);
  await noOverflow(`${viewport.name}: ground diagram has no horizontal overflow`,'#panel-geothermal');
  if(viewport.width>850){await page.locator('#toggle-season').click();check(`${viewport.name}: global season toggle also refreshes the card`,await page.locator('#geo-summer').getAttribute('aria-pressed')==='true'&&(await page.locator('#geo-season').innerText()).includes('Summer sends room heat'));}
  const path=page.locator('#panel-geothermal > details').first();await path.locator('summary').click();
  check(`${viewport.name}: full path identifies both room heat collectors and excludes groundwater`,(await path.innerText()).includes('rear-door water coils')&&(await path.innerText()).includes('Electrical rooms use fan coils')&&(await path.innerText()).includes('do not carry air into the building or draw groundwater'));
  await noOverflow(`${viewport.name}: expanded ground explanation fits`,'#panel-geothermal');
  await page.locator('#tab-geothermal').focus();await page.keyboard.press('ArrowRight');
  check(`${viewport.name}: ground card keyboard wraps and restores overview`,await page.locator('#panel-overview').isVisible()&&JSON.stringify(await snapshotOverview())===JSON.stringify(original)&&page.url()===url);
  await path.evaluate(element=>element.open=false);
  for(const stop of [4,5,9]){
   await atStop(stop);const original=await snapshotOverview(),url=page.url();await page.locator('#tab-freeze').click();
   check(`${viewport.name} stop ${stop}: winter protection is an inline fourth card`,await page.locator('#panel-freeze').isVisible()&&page.url()===url&&await page.locator('#card-count').textContent()==='4 / 4');
   const text=await page.locator('#panel-freeze').textContent();
   check(`${viewport.name} stop ${stop}: fluid circuits and outage trigger are distinct`,text.includes('separate rack circuits use PG25')&&text.includes('If the computers stop during a long cold outage')&&text.includes('high teens °F')&&text.includes('2°F (−16°C)'));
   check(`${viewport.name} stop ${stop}: heat path explains liquid transport and outdoor air`,text.includes('running computers are the heat source')&&text.includes('no hot-air duct')&&text.includes('Outside air passes over the tubes and fins'));
   check(`${viewport.name} stop ${stop}: cold snap protection does not rely on aggregate heat alone`,text.includes('worst-case cold-snap heat balance')&&text.includes('does not by itself protect every outdoor coil')&&text.includes('air-assisted drainage'));
   await noOverflow(`${viewport.name} stop ${stop}: freeze card has no horizontal overflow`,'#panel-freeze');
   if(stop===5)await capture(`${viewport.name}-freeze`);
   await page.locator('#card-next').click();check(`${viewport.name} stop ${stop}: winter card restores the unchanged overview`,await page.locator('#panel-overview').isVisible()&&JSON.stringify(await snapshotOverview())===JSON.stringify(original));
  }
 }
 await page.setViewportSize({width:1920,height:1080});await atStop(0);await page.locator('#tab-closer').click();
 check('Equipment selector exposes 29 unique choices',new Set(await page.locator('#object-select option').evaluateAll(elements=>elements.map(element=>element.value))).size===29);
 for(const [key,object] of Object.entries(content.objects)){
  await page.locator('#object-select').selectOption(key);
  check(`Equipment ${key}: selector updates the displayed card`,await page.locator('#headline').textContent()===object.name&&await page.locator('#object-title').textContent()===object.name&&await page.evaluate(key=>SEED.state.object===key,key));
 }
 // These real buttons cross from explanations into the corresponding geometry.
 for(const key of ['bypass','drainTanks']){
  await atStop(5);await page.locator('#tab-freeze').click();const before=await page.evaluate(()=>SEED.camera.position.toArray());
  await page.locator(`#panel-freeze [data-system-view="${key}"]`).click();await settled();
  check(`Freeze action ${key}: focuses hardware and opens its explanation`,await page.locator('#panel-closer').isVisible()&&await page.evaluate(({key,before})=>SEED.state.object===key&&SEED.state.exploring&&SEED.camera.position.toArray().some((v,i)=>Math.abs(v-before[i])>1),{key,before}));
 }
 await atStop(6);await page.locator('#tab-geothermal').click();await page.locator('#panel-geothermal [data-system-view="coldInsulation"]').click();await settled();
 check('Ground action focuses insulated Cold Battery House pipes',await page.evaluate(()=>SEED.state.object==='coldInsulation'&&SEED.state.ground&&SEED.state.exploring));
 for(const key of newEquipment){
  await atStop(0);await page.locator('#tab-closer').click();await page.locator('#object-select').selectOption(key);await page.locator(`#object-description [data-system-view="${key}"]`).click();await settled();
  check(`New hardware ${key}: geometry exists and is revealed`,await page.evaluate(key=>{const group=SEED.groups[key];if(!group)return false;let count=0;group.traverse(object=>{if(object.isMesh&&object.visible)count++;});return group.visible&&count>0;},key));
  const point=await actualMeshPoint(key);check(`New hardware ${key}: exposed by its camera view`,!!point);
  await page.mouse.move(700,100);await page.mouse.move(point.x,point.y);await page.waitForTimeout(120);
  check(`New hardware ${key}: real geometry hover identifies it`,await page.locator('#tooltip').isVisible()&&await page.locator('#tooltip').textContent()===content.objects[key].name);
  await page.mouse.click(point.x,point.y);
  check(`New hardware ${key}: real geometry click opens its card`,await page.locator('#panel-closer').isVisible()&&await page.locator('#headline').textContent()===content.objects[key].name);
  await capture(`hardware-${key}`);
  const stop=await page.evaluate(()=>SEED.state.index);await page.locator('#next').click();await settled();
  check(`New hardware ${key}: Next resumes the tour after focus`,await page.evaluate(stop=>SEED.state.index===stop+1&&!SEED.state.exploring&&SEED.state.card===0,stop));
 }
 check('Thermal explanations never open an external page',context.pages().length===1&&page.url().startsWith('http://127.0.0.1:4173/'));
 check('No browser errors',report.errors.length===0);check('No failed assets',report.network.length===0);report.passed=true;
}catch(error){report.failure=String(error);console.error(error);await capture('failure');}
finally{fs.writeFileSync('qa/thermal-design-report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify({passed:report.passed,checks:report.checks.length,failure:report.failure,screenshots:report.screenshots.length}));if(!report.passed)process.exitCode=1;}
